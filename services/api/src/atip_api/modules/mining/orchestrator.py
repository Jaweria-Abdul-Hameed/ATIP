"""Analysis pipeline orchestrator for repository mining, static analysis, and progress tracking (M3-05)."""

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.job import ExecutionJob, JobStatus
from atip_api.db.models.mining import AnalysisRun
from atip_api.db.models.repository import Repository
from atip_api.modules.mining.dependency_graph import DependencyGraphBuilder
from atip_api.modules.mining.git_fetcher import SafeGitFetcher
from atip_api.modules.mining.history_miner import HistoryMiner
from atip_api.modules.mining.snapshot import SnapshotManager
from atip_api.modules.mining.static_analyzer import (
    CodeComplexityAnalyzer,
    TestDiscoverer,
)

logger = logging.getLogger(__name__)


class AnalysisPipelineOrchestrator:
    """Orchestrates M3-01 through M3-04 mining pipeline with progress state machine and durable persistence."""

    def __init__(self, git_fetcher: SafeGitFetcher | None = None) -> None:
        self.git_fetcher = git_fetcher or SafeGitFetcher()
        self.snapshot_mgr = SnapshotManager(git_fetcher=self.git_fetcher)
        self.history_miner = HistoryMiner(git_fetcher=self.git_fetcher)
        self.dep_builder = DependencyGraphBuilder(git_fetcher=self.git_fetcher)

    async def run_pipeline(
        self,
        session: AsyncSession,
        repository: Repository,
        job: ExecutionJob,
        analysis_run: AnalysisRun,
        repo_path: str = ".",
        target_commit_or_ref: str = "HEAD",
    ) -> AnalysisRun:
        """Execute end-to-end repository analysis pipeline."""
        try:
            # 1. Provisioning & Snapshot resolution (M3-01)
            job.status = JobStatus.PROVISIONING
            job.progress_pct = 15
            job.current_step = "Resolving immutable commit snapshot"
            job.started_at = datetime.now(UTC).isoformat()
            await session.commit()

            snapshot = await self.snapshot_mgr.get_or_create_snapshot(
                session=session,
                org_id=repository.organization_id,
                repository=repository,
                ref_or_commit=target_commit_or_ref,
                local_repo_path=repo_path,
            )
            resolved_sha = snapshot.commit_sha
            analysis_run.commit_sha = resolved_sha
            analysis_run.status = "running"
            await session.commit()

            # 2. History Mining, Diffs, and Hotspots (M3-02)
            job.status = JobStatus.RUNNING
            job.progress_pct = 35
            job.current_step = "Mining commit history, file diffs, and churn hotspots"
            await session.commit()

            await self.history_miner.mine_repository_history(
                session=session,
                org_id=repository.organization_id,
                repository=repository,
                branch=analysis_run.branch,
                max_commits=100,
                include_patch=True,
                local_repo_path=repo_path,
            )
            await self.history_miner.compute_hotspots_and_ownership(
                session=session,
                repository_id=repository.id,
                org_id=repository.organization_id,
            )

            # 3. Dependency Graph & Circular Cycles (M3-03)
            job.progress_pct = 60
            job.current_step = "Building dependency graph and cycle detection"
            await session.commit()

            graph_data = await self.dep_builder.build_and_persist_graph(
                session=session,
                org_id=repository.organization_id,
                repository_id=repository.id,
                commit_sha=resolved_sha,
                repo_path=repo_path,
            )
            analysis_run.dependency_count = graph_data.get("total_edges", 0)

            # 4. Static Complexity and Test Discovery (M3-04)
            job.progress_pct = 80
            job.current_step = "Analyzing static complexity and discovering test suites"
            await session.commit()

            tree_files = await self.git_fetcher.list_tree_files(repo_path, resolved_sha)
            source_exts = {".py", ".pyw", ".ts", ".tsx", ".js", ".jsx"}
            test_exts = {".py", ".pyw", ".ts", ".tsx", ".js", ".jsx"}

            total_files = 0
            total_lines = 0
            languages_stats: dict[str, dict[str, int]] = defaultdict(
                lambda: {"files": 0, "lines": 0}
            )
            file_complexities: list[dict[str, Any]] = []
            test_cases: list[dict[str, Any]] = []

            for f in tree_files:
                p = f["path"]
                if p.startswith("node_modules/") or p.startswith(".git/"):
                    continue

                is_source = any(p.endswith(ext) for ext in source_exts)
                if not is_source:
                    continue

                try:
                    content_bytes = await self.git_fetcher.read_file_at_commit(
                        repo_path, resolved_sha, p
                    )
                    text = content_bytes.decode("utf-8", errors="replace")
                except Exception as read_err:
                    logger.warning("Could not read file %s at %s: %s", p, resolved_sha, read_err)
                    continue

                total_files += 1
                metric = CodeComplexityAnalyzer.analyze_source(text, p)
                total_lines += metric.lines_total
                languages_stats[metric.language]["files"] += 1
                languages_stats[metric.language]["lines"] += metric.lines_total

                file_complexities.append(
                    {
                        "file_path": metric.file_path,
                        "language": metric.language,
                        "lines_total": metric.lines_total,
                        "lines_code": metric.lines_code,
                        "cyclomatic_complexity": metric.cyclomatic_complexity,
                        "maintainability_index": metric.maintainability_index,
                        "functions_count": len(metric.functions),
                    }
                )

                # Test discovery
                is_test_candidate = (
                    "test" in p.lower()
                    or "spec" in p.lower()
                    or p.endswith(
                        ("_test.py", "test_.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js")
                    )
                )
                if is_test_candidate and any(p.endswith(ext) for ext in test_exts):
                    cases = TestDiscoverer.discover_in_file(text, p)
                    for c in cases:
                        test_cases.append(
                            {
                                "file_path": c.file_path,
                                "suite_name": c.suite_name,
                                "test_name": c.test_name,
                                "line_number": c.line_number,
                                "framework": c.framework,
                                "language": c.language,
                            }
                        )

            avg_complexity = (
                round(
                    sum(fc["cyclomatic_complexity"] for fc in file_complexities)
                    / len(file_complexities),
                    1,
                )
                if file_complexities
                else 1.0
            )
            avg_maintainability = (
                round(
                    sum(fc["maintainability_index"] for fc in file_complexities)
                    / len(file_complexities),
                    1,
                )
                if file_complexities
                else 100.0
            )

            complexity_summary = {
                "analyzed_files_count": len(file_complexities),
                "average_cyclomatic_complexity": avg_complexity,
                "average_maintainability_index": avg_maintainability,
                "highest_complexity_files": sorted(
                    file_complexities, key=lambda x: x["cyclomatic_complexity"], reverse=True
                )[:10],
            }

            # 5. Persist Results & Transition to COMPLETED
            job.status = JobStatus.COMPLETED
            job.progress_pct = 100
            job.current_step = "Analysis completed successfully"
            job.completed_at = datetime.now(UTC).isoformat()

            analysis_run.status = "completed"
            analysis_run.total_files = total_files
            analysis_run.total_lines = total_lines
            analysis_run.languages_json = dict(languages_stats)
            analysis_run.complexity_summary = complexity_summary
            analysis_run.test_inventory = test_cases
            analysis_run.completed_at = datetime.now(UTC)

            await session.commit()
            return analysis_run

        except Exception as exc:
            logger.exception("Analysis pipeline encountered an error: %s", exc)
            job.status = JobStatus.FAILED
            job.progress_pct = 0
            job.current_step = f"Analysis failed: {exc}"
            job.error_message = str(exc)
            job.completed_at = datetime.now(UTC).isoformat()

            analysis_run.status = "failed"
            analysis_run.completed_at = datetime.now(UTC)
            await session.commit()
            raise
