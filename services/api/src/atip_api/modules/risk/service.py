"""Risk assessment service orchestrating deterministic scoring, impact propagation, and persistence."""

import logging
import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.mining import (
    AnalysisRun,
    CommitRecord,
    DependencyEdgeRecord,
    FileChangeRecord,
)
from atip_api.db.models.repository import Repository
from atip_api.db.models.risk import RiskAssessment
from atip_api.modules.risk.engine import (
    DeterministicRiskEngine,
    DeterministicRiskModelConfig,
)
from atip_api.modules.risk.impact import ChangeImpactAnalyzer
from atip_api.modules.risk.schemas import (
    FileRiskAssessmentRead,
    RiskAssessmentSummaryRead,
)
from atip_api.modules.risk.test_selector import (
    ImpactedTestSelector,
    TestSelectionResult,
)

logger = logging.getLogger(__name__)

DEFECT_KEYWORDS = ("fix", "bug", "patch", "resolve", "defect", "issue", "hotfix", "regression")


class RiskAssessmentService:
    """Service orchestrating explainable risk calculation, impact analysis, and persistence."""

    def __init__(
        self,
        config: DeterministicRiskModelConfig | None = None,
        impact_analyzer: ChangeImpactAnalyzer | None = None,
        test_selector: ImpactedTestSelector | None = None,
    ):
        self.config = config or DeterministicRiskModelConfig()
        self.engine = DeterministicRiskEngine(self.config)
        self.impact_analyzer = impact_analyzer or ChangeImpactAnalyzer()
        self.test_selector = test_selector or ImpactedTestSelector(self.impact_analyzer)

    async def get_or_create_assessment(
        self,
        session: AsyncSession,
        org_id: str,
        repository_id: str,
        commit_sha: str | None = None,
        branch: str = "main",
        force_recompute: bool = False,
    ) -> RiskAssessmentSummaryRead:
        """
        Retrieves existing risk assessment or computes a fresh deterministic assessment
        grounded in repository mining, static analysis, dependencies, and git history.
        """
        # If not forcing recompute, check for cached assessment
        if not force_recompute:
            stmt = (
                select(RiskAssessment)
                .where(
                    RiskAssessment.organization_id == org_id,
                    RiskAssessment.repository_id == repository_id,
                )
            )
            if commit_sha:
                stmt = stmt.where(RiskAssessment.commit_sha == commit_sha)
            else:
                stmt = stmt.where(RiskAssessment.branch == branch)
            stmt = stmt.order_by(desc(RiskAssessment.created_at)).limit(1)

            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return self._assessment_model_to_summary(existing)

        # Compute fresh assessment
        return await self.compute_and_persist_assessment(
            session=session,
            org_id=org_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
            branch=branch,
        )

    async def compute_and_persist_assessment(
        self,
        session: AsyncSession,
        org_id: str,
        repository_id: str,
        commit_sha: str | None = None,
        branch: str = "main",
    ) -> RiskAssessmentSummaryRead:
        """Computes full risk assessment across all mined evidence and persists record."""
        # 1. Fetch repository
        repo_stmt = select(Repository).where(
            Repository.id == repository_id,
            Repository.organization_id == org_id,
        )
        repo_res = await session.execute(repo_stmt)
        repo = repo_res.scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository '{repository_id}' not found for tenant '{org_id}'")

        # 2. Fetch latest or target AnalysisRun
        analysis_stmt = (
            select(AnalysisRun)
            .where(
                AnalysisRun.organization_id == org_id,
                AnalysisRun.repository_id == repository_id,
            )
        )
        if commit_sha:
            analysis_stmt = analysis_stmt.where(AnalysisRun.commit_sha == commit_sha)
        else:
            analysis_stmt = analysis_stmt.order_by(desc(AnalysisRun.created_at))
        analysis_stmt = analysis_stmt.limit(1)

        analysis_res = await session.execute(analysis_stmt)
        analysis_run = analysis_res.scalar_one_or_none()

        target_sha = commit_sha or (analysis_run.commit_sha if analysis_run else "HEAD")

        # 3. Fetch Dependency Edges
        dep_stmt = (
            select(DependencyEdgeRecord)
            .where(
                DependencyEdgeRecord.organization_id == org_id,
                DependencyEdgeRecord.repository_id == repository_id,
            )
        )
        dep_res = await session.execute(dep_stmt)
        dep_records = dep_res.scalars().all()
        dep_edges = [
            {
                "source_file": edge.source_file,
                "target_file": edge.target_file or edge.target_module,
                "target_module": edge.target_module,
            }
            for edge in dep_records
        ]
        graph_available = len(dep_edges) > 0

        # 4. Fetch Commits & File Changes to compute churn & defect history
        commit_stmt = (
            select(CommitRecord)
            .where(
                CommitRecord.organization_id == org_id,
                CommitRecord.repository_id == repository_id,
            )
            .order_by(desc(CommitRecord.committed_at))
            .limit(100)
        )
        commit_res = await session.execute(commit_stmt)
        commits = commit_res.scalars().all()
        total_commits = len(commits)

        # Identify bug-fix commits
        defect_commit_shas: set[str] = set()
        for c in commits:
            msg_lower = (c.message or "").lower()
            if any(k in msg_lower for k in DEFECT_KEYWORDS):
                defect_commit_shas.add(c.commit_sha)

        # File churn and defect mapping
        fch_stmt = (
            select(FileChangeRecord)
            .where(
                FileChangeRecord.organization_id == org_id,
                FileChangeRecord.repository_id == repository_id,
            )
        )
        fch_res = await session.execute(fch_stmt)
        file_changes = fch_res.scalars().all()

        file_churn_counts: dict[str, int] = {}
        file_lines_changed: dict[str, int] = {}
        file_defect_counts: dict[str, int] = {}
        changed_in_target_commit: list[str] = []

        for fc in file_changes:
            path = fc.file_path
            file_churn_counts[path] = file_churn_counts.get(path, 0) + 1
            file_lines_changed[path] = file_lines_changed.get(path, 0) + (fc.insertions + fc.deletions)
            if fc.commit_sha in defect_commit_shas:
                file_defect_counts[path] = file_defect_counts.get(path, 0) + 1
            if fc.commit_sha == target_sha:
                changed_in_target_commit.append(path)

        # 5. Extract Complexity & Tests from AnalysisRun
        file_complexity_map: dict[str, dict[str, Any]] = {}
        test_inventory: list[dict[str, Any]] = []
        coverage_map: dict[str, float] = {}

        if analysis_run:
            if analysis_run.complexity_summary and "highest_complexity_files" in analysis_run.complexity_summary:
                for fc in analysis_run.complexity_summary.get("highest_complexity_files", []):
                    file_complexity_map[fc.get("file_path", "")] = fc

            test_inventory = analysis_run.test_inventory or []
            if analysis_run.coverage_summary and "files" in analysis_run.coverage_summary:
                for cov_f in analysis_run.coverage_summary.get("files", []):
                    coverage_map[cov_f.get("file_path", "")] = cov_f.get("coverage_pct", 0.0)

        all_test_paths = [t.get("file_path", "") for t in test_inventory if t.get("file_path")]

        # 6. Gather all unique files to evaluate
        all_candidate_files: set[str] = set()
        all_candidate_files.update(file_churn_counts.keys())
        all_candidate_files.update(file_complexity_map.keys())
        for e in dep_edges:
            all_candidate_files.add(e["source_file"])
            if e.get("target_file"):
                all_candidate_files.add(e["target_file"])

        # Filter out common test files from primary risk evaluation (tests are evaluated for test selection)
        source_files = [
            f for f in all_candidate_files
            if f and not any(f.endswith(ext) for ext in ["_test.py", "test_.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js"])
            and "test" not in f.lower()
        ]

        if not source_files and all_candidate_files:
            source_files = list(all_candidate_files)

        # 7. Evaluate each file
        file_assessments: list[FileRiskAssessmentRead] = []
        for file_path in source_files:
            comp = file_complexity_map.get(file_path, {})
            cyclomatic = comp.get("cyclomatic_complexity")
            mi = comp.get("maintainability_index")
            loc = comp.get("lines_code") or comp.get("lines_total")

            churn_count = file_churn_counts.get(file_path, 1 if file_path in changed_in_target_commit else 0)
            lines_ch = file_lines_changed.get(file_path, 0)

            direct_deps, trans_deps = self.impact_analyzer.compute_blast_radius_counts(file_path, dep_edges)

            cov_pct = coverage_map.get(file_path)
            associated_tests = self.test_selector.find_associated_test_files(file_path, all_test_paths)
            has_test_file = len(associated_tests) > 0
            defect_count = file_defect_counts.get(file_path, 0)

            assmt = self.engine.evaluate_file(
                file_path=file_path,
                cyclomatic=cyclomatic,
                maintainability_index=mi,
                loc=loc,
                churn_count=churn_count,
                lines_changed=lines_ch,
                direct_dependents=direct_deps,
                transitive_dependents=trans_deps,
                coverage_pct=cov_pct,
                has_test_file=has_test_file,
                defect_commit_count=defect_count,
                associated_tests=associated_tests,
                total_repo_commits=total_commits,
                graph_available=graph_available,
                tests_discovered=len(test_inventory) > 0,
            )
            file_assessments.append(assmt)

        # 8. Compute Change-Impact Propagation Nodes
        target_changed_list = changed_in_target_commit or (source_files[:5] if source_files else [])
        impacted_nodes = self.impact_analyzer.compute_impact(target_changed_list, dep_edges)

        # 9. Aggregate Repository Risk Summary
        assessment_id = f"rsk_{uuid.uuid4().hex[:16]}"
        summary = self.engine.evaluate_repository(
            assessment_id=assessment_id,
            repository_id=repository_id,
            commit_sha=target_sha,
            branch=branch,
            file_assessments=file_assessments,
        )
        summary.impacted_nodes = impacted_nodes

        # 10. Persist in database
        db_record = RiskAssessment(
            id=assessment_id,
            repository_id=repository_id,
            commit_sha=target_sha,
            branch=branch,
            model_version=summary.model_version,
            model_type=summary.model_type,
            overall_score=summary.overall_score,
            risk_tier=summary.risk_tier,
            confidence=summary.confidence,
            has_missing_data=summary.has_missing_data,
            feature_weights=summary.feature_weights,
            file_assessments=[f.model_dump() for f in summary.files],
            summary_stats=summary.summary_stats,
            analysis_run_id=analysis_run.id if analysis_run else None,
            evaluated_at=summary.evaluated_at,
            organization_id=org_id,
        )
        session.add(db_record)
        await session.commit()

        return summary

    def _assessment_model_to_summary(self, model: RiskAssessment) -> RiskAssessmentSummaryRead:
        """Converts database model into typed response schema."""
        raw_files = model.file_assessments or []
        files = [FileRiskAssessmentRead(**f) for f in raw_files]
        return RiskAssessmentSummaryRead(
            id=model.id,
            repository_id=model.repository_id,
            commit_sha=model.commit_sha,
            branch=model.branch,
            model_version=model.model_version,
            model_type=model.model_type,
            overall_score=model.overall_score,
            risk_tier=model.risk_tier,
            confidence=model.confidence,
            has_missing_data=model.has_missing_data,
            feature_weights=model.feature_weights or {},
            summary_stats=model.summary_stats or {},
            evaluated_at=model.evaluated_at or model.created_at,
            files=files,
            impacted_nodes=[],
        )

    async def get_test_selection(
        self,
        session: AsyncSession,
        org_id: str,
        repository_id: str,
        commit_sha: str | None = None,
    ) -> TestSelectionResult:
        """Computes impacted regression test suite and flags test gaps."""
        # Retrieve risk summary
        summary = await self.get_or_create_assessment(
            session=session,
            org_id=org_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
        )

        # Retrieve analysis run tests and dependency edges
        analysis_stmt = (
            select(AnalysisRun)
            .where(
                AnalysisRun.organization_id == org_id,
                AnalysisRun.repository_id == repository_id,
            )
            .order_by(desc(AnalysisRun.created_at))
            .limit(1)
        )
        a_res = await session.execute(analysis_stmt)
        analysis_run = a_res.scalar_one_or_none()
        tests = (analysis_run.test_inventory or []) if analysis_run else []

        dep_stmt = (
            select(DependencyEdgeRecord)
            .where(
                DependencyEdgeRecord.organization_id == org_id,
                DependencyEdgeRecord.repository_id == repository_id,
            )
        )
        dep_res = await session.execute(dep_stmt)
        dep_records = dep_res.scalars().all()
        dep_edges = [
            {
                "source_file": edge.source_file,
                "target_file": edge.target_file or edge.target_module,
            }
            for edge in dep_records
        ]

        # Top risky files as changed candidates if none specified
        changed = [f.file_path for f in summary.files[:5]]
        file_risks = {f.file_path: f.risk_score for f in summary.files}

        return self.test_selector.select_tests(
            repository_id=repository_id,
            commit_sha=summary.commit_sha,
            changed_files=changed,
            dependency_edges=dep_edges,
            all_discovered_tests=tests,
            file_risks=file_risks,
        )
