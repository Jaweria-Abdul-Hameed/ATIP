"""Deterministic versioned risk model with explainable feature weights and missing-data handling."""

from dataclasses import dataclass
from datetime import datetime

from atip_api.modules.risk.schemas import (
    FileRiskAssessmentRead,
    RiskAssessmentSummaryRead,
    RiskFactorRead,
)


@dataclass
class DeterministicRiskModelConfig:
    """Configurable and versioned weights for the deterministic risk model."""

    version: str = "deterministic-v1.0.0"
    model_type: str = "deterministic"

    # Explainable feature weights (must sum to 1.0)
    weight_complexity: float = 0.25
    weight_churn: float = 0.25
    weight_blast_radius: float = 0.25
    weight_coverage_gap: float = 0.15
    weight_defect_history: float = 0.10

    # Complexity thresholds
    cyclomatic_threshold_low: int = 5
    cyclomatic_threshold_medium: int = 15
    cyclomatic_threshold_high: int = 30
    mi_threshold_warning: float = 50.0

    # Churn thresholds
    churn_threshold_medium: int = 3
    churn_threshold_high: int = 8
    churn_lines_threshold: int = 250

    # Blast radius thresholds
    blast_radius_threshold_medium: int = 3
    blast_radius_threshold_high: int = 8

    # Coverage thresholds
    coverage_threshold_high: float = 80.0
    coverage_threshold_medium: float = 50.0

    def as_weights_dict(self) -> dict[str, float]:
        return {
            "complexity": self.weight_complexity,
            "churn": self.weight_churn,
            "blast_radius": self.weight_blast_radius,
            "coverage_gap": self.weight_coverage_gap,
            "defect_history": self.weight_defect_history,
        }


def compute_risk_tier(score: int) -> str:
    """Maps a 0..100 risk score to an explainable categorical tier."""
    if score >= 85:
        return "critical"
    elif score >= 65:
        return "high"
    elif score >= 35:
        return "medium"
    return "low"


class DeterministicRiskEngine:
    """Engine computing transparent, deterministic, and versioned defect-risk scores."""

    def __init__(self, config: DeterministicRiskModelConfig | None = None):
        self.config = config or DeterministicRiskModelConfig()

    def evaluate_complexity_factor(
        self,
        cyclomatic: int | None,
        maintainability_index: float | None,
        loc: int | None,
    ) -> RiskFactorRead:
        """Evaluates static complexity factor and handles missing AST/parse data."""
        weight = self.config.weight_complexity

        if cyclomatic is None:
            # Missing complexity data: fallback to LOC proxy if available
            if loc is not None and loc > 0:
                loc_proxy_score = min(60.0, (loc / 20.0) * 10.0)
                return RiskFactorRead(
                    factor_key="complexity",
                    name="Code Complexity & Maintainability",
                    raw_value={"loc": loc, "proxy": "loc_heuristic"},
                    normalized_score=loc_proxy_score,
                    weight=weight,
                    weighted_score=round(loc_proxy_score * weight, 2),
                    impact=compute_risk_tier(int(loc_proxy_score)),
                    description=f"Direct complexity unparsed; approximated from file size ({loc} LOC).",
                    confidence=0.45,
                    is_missing=True,
                    missing_reason="AST parser did not produce cyclomatic metrics for this file.",
                )
            else:
                # Completely missing
                default_score = 30.0
                return RiskFactorRead(
                    factor_key="complexity",
                    name="Code Complexity & Maintainability",
                    raw_value=None,
                    normalized_score=default_score,
                    weight=weight,
                    weighted_score=round(default_score * weight, 2),
                    impact="low",
                    description="No complexity or LOC data available. Default neutral score assigned.",
                    confidence=0.30,
                    is_missing=True,
                    missing_reason="No syntax analysis or line count data available.",
                )

        # We have actual cyclomatic complexity
        if cyclomatic <= self.config.cyclomatic_threshold_low:
            base_score = 10.0
            impact = "low"
        elif cyclomatic <= self.config.cyclomatic_threshold_medium:
            base_score = 35.0
            impact = "medium"
        elif cyclomatic <= self.config.cyclomatic_threshold_high:
            base_score = 75.0
            impact = "high"
        else:
            base_score = 95.0
            impact = "critical"

        # Maintainability penalty
        mi_penalty = 0.0
        if maintainability_index is not None and maintainability_index < self.config.mi_threshold_warning:
            mi_penalty = 15.0

        normalized_score = min(100.0, base_score + mi_penalty)
        impact = compute_risk_tier(int(normalized_score))
        mi_text = f", MI: {maintainability_index:.1f}" if maintainability_index is not None else ""
        desc = (
            f"Cyclomatic complexity of {cyclomatic}{mi_text}. "
            f"Evaluated as {impact} complexity risk."
        )

        return RiskFactorRead(
            factor_key="complexity",
            name="Code Complexity & Maintainability",
            raw_value={"cyclomatic": cyclomatic, "maintainability_index": maintainability_index, "loc": loc},
            normalized_score=normalized_score,
            weight=weight,
            weighted_score=round(normalized_score * weight, 2),
            impact=impact,
            description=desc,
            confidence=0.95,
            is_missing=False,
            missing_reason=None,
        )

    def evaluate_churn_factor(
        self,
        churn_count: int | None,
        lines_changed: int | None,
        total_repo_commits: int = 10,
    ) -> RiskFactorRead:
        """Evaluates historical change frequency and modification volume."""
        weight = self.config.weight_churn

        if churn_count is None:
            return RiskFactorRead(
                factor_key="churn",
                name="Change Frequency & Churn",
                raw_value=None,
                normalized_score=25.0,
                weight=weight,
                weighted_score=round(25.0 * weight, 2),
                impact="low",
                description="Commit churn history unavailable. Assigned neutral baseline.",
                confidence=0.40,
                is_missing=True,
                missing_reason="File commit history has not been mined.",
            )

        if total_repo_commits < 3:
            # Very shallow repository history
            score = 25.0 if churn_count <= 1 else 50.0
            return RiskFactorRead(
                factor_key="churn",
                name="Change Frequency & Churn",
                raw_value={"churn_count": churn_count, "lines_changed": lines_changed or 0},
                normalized_score=score,
                weight=weight,
                weighted_score=round(score * weight, 2),
                impact=compute_risk_tier(int(score)),
                description=f"Shallow commit history ({total_repo_commits} commits mined). Churn count: {churn_count}.",
                confidence=0.55,
                is_missing=True,
                missing_reason="Repository history contains fewer than 3 commits.",
            )

        # Standard churn evaluation
        lines = lines_changed or 0
        if churn_count <= 1:
            score = 10.0
            impact = "low"
        elif churn_count <= self.config.churn_threshold_medium:
            score = 40.0
            impact = "medium"
        elif churn_count <= self.config.churn_threshold_high:
            score = 70.0
            impact = "high"
        else:
            score = 90.0
            impact = "critical"

        # High line volume modifier
        if lines >= self.config.churn_lines_threshold:
            score = min(100.0, score + 15.0)

        impact = compute_risk_tier(int(score))
        desc = f"Modified in {churn_count} commits ({lines} lines churned across history)."

        return RiskFactorRead(
            factor_key="churn",
            name="Change Frequency & Churn",
            raw_value={"churn_count": churn_count, "lines_changed": lines},
            normalized_score=score,
            weight=weight,
            weighted_score=round(score * weight, 2),
            impact=impact,
            description=desc,
            confidence=0.95,
            is_missing=False,
            missing_reason=None,
        )

    def evaluate_blast_radius_factor(
        self,
        direct_dependents: int | None,
        transitive_dependents: int | None,
        graph_available: bool = True,
    ) -> RiskFactorRead:
        """Evaluates downstream architectural impact from the dependency graph."""
        weight = self.config.weight_blast_radius

        if not graph_available or direct_dependents is None:
            return RiskFactorRead(
                factor_key="blast_radius",
                name="Dependency Blast Radius",
                raw_value=None,
                normalized_score=30.0,
                weight=weight,
                weighted_score=round(30.0 * weight, 2),
                impact="low",
                description="Dependency graph unmined or unavailable. Conservative neutral radius assumed.",
                confidence=0.45,
                is_missing=True,
                missing_reason="Dependency edges have not been extracted for this commit snapshot.",
            )

        transitive = transitive_dependents if transitive_dependents is not None else direct_dependents
        total_impacted = max(direct_dependents, transitive)

        if total_impacted == 0:
            score = 10.0
            impact = "low"
            desc = "Isolated file with 0 downstream dependents."
        elif total_impacted <= self.config.blast_radius_threshold_medium:
            score = 45.0
            impact = "medium"
            desc = f"Imported directly by {direct_dependents} file(s) ({total_impacted} transitive)."
        elif total_impacted <= self.config.blast_radius_threshold_high:
            score = 75.0
            impact = "high"
            desc = f"Significant blast radius: {direct_dependents} direct, {total_impacted} transitive dependents."
        else:
            score = 95.0
            impact = "critical"
            desc = f"Critical architectural core: {total_impacted} downstream dependents impacted by changes."

        return RiskFactorRead(
            factor_key="blast_radius",
            name="Dependency Blast Radius",
            raw_value={"direct": direct_dependents, "transitive": transitive},
            normalized_score=score,
            weight=weight,
            weighted_score=round(score * weight, 2),
            impact=impact,
            description=desc,
            confidence=0.92,
            is_missing=False,
            missing_reason=None,
        )

    def evaluate_coverage_gap_factor(
        self,
        coverage_pct: float | None,
        has_test_file: bool,
        tests_discovered: bool = True,
    ) -> RiskFactorRead:
        """Evaluates presence of tests and measured coverage percentage."""
        weight = self.config.weight_coverage_gap

        if not tests_discovered and coverage_pct is None:
            return RiskFactorRead(
                factor_key="coverage_gap",
                name="Test Coverage Gap",
                raw_value=None,
                normalized_score=60.0,
                weight=weight,
                weighted_score=round(60.0 * weight, 2),
                impact="medium",
                description="Test discovery and coverage ingestion pending. Moderate gap assumed.",
                confidence=0.40,
                is_missing=True,
                missing_reason="Test inventory and coverage reports have not been ingested.",
            )

        if coverage_pct is not None:
            # We have measured coverage
            if coverage_pct >= self.config.coverage_threshold_high:
                score = 10.0
                impact = "low"
                desc = f"Well covered by tests ({coverage_pct:.1f}% line coverage)."
            elif coverage_pct >= self.config.coverage_threshold_medium:
                score = 50.0
                impact = "medium"
                desc = f"Moderate test coverage ({coverage_pct:.1f}% line coverage)."
            else:
                score = 85.0
                impact = "high"
                desc = f"Low test coverage ({coverage_pct:.1f}% line coverage leaves significant regression risk)."

            return RiskFactorRead(
                factor_key="coverage_gap",
                name="Test Coverage Gap",
                raw_value={"coverage_pct": coverage_pct, "has_test_file": has_test_file},
                normalized_score=score,
                weight=weight,
                weighted_score=round(score * weight, 2),
                impact=impact,
                description=desc,
                confidence=0.95,
                is_missing=False,
                missing_reason=None,
            )

        # Coverage report not ingested, but test file presence known
        if has_test_file:
            score = 35.0
            desc = "Associated test file discovered, but measured line coverage report not yet ingested."
            conf = 0.75
            missing = False
            reason = None
        else:
            score = 85.0
            desc = "No associated test file found and no coverage report available."
            conf = 0.85
            missing = False
            reason = None

        return RiskFactorRead(
            factor_key="coverage_gap",
            name="Test Coverage Gap",
            raw_value={"has_test_file": has_test_file, "coverage_pct": None},
            normalized_score=score,
            weight=weight,
            weighted_score=round(score * weight, 2),
            impact=compute_risk_tier(int(score)),
            description=desc,
            confidence=conf,
            is_missing=missing,
            missing_reason=reason,
        )

    def evaluate_defect_history_factor(
        self,
        defect_commit_count: int | None,
    ) -> RiskFactorRead:
        """Evaluates whether the file was historically altered in defect/bug-fix commits."""
        weight = self.config.weight_defect_history

        if defect_commit_count is None:
            return RiskFactorRead(
                factor_key="defect_history",
                name="Historical Defect Proneness",
                raw_value=None,
                normalized_score=20.0,
                weight=weight,
                weighted_score=round(20.0 * weight, 2),
                impact="low",
                description="Defect-linked commit mining not performed. Low baseline assumed.",
                confidence=0.50,
                is_missing=True,
                missing_reason="Historical commit messages were not parsed for defect keywords.",
            )

        if defect_commit_count == 0:
            score = 10.0
            impact = "low"
            desc = "No prior bug-fix or hotfix commits associated with this file."
        elif defect_commit_count == 1:
            score = 45.0
            impact = "medium"
            desc = "Modified in 1 prior defect/bug-fix commit."
        elif defect_commit_count <= 3:
            score = 75.0
            impact = "high"
            desc = f"Recurrent defect history: modified in {defect_commit_count} prior bug-fix commits."
        else:
            score = 95.0
            impact = "critical"
            desc = f"Defect hotspot: modified in {defect_commit_count} prior bug-fix commits."

        return RiskFactorRead(
            factor_key="defect_history",
            name="Historical Defect Proneness",
            raw_value={"defect_commit_count": defect_commit_count},
            normalized_score=score,
            weight=weight,
            weighted_score=round(score * weight, 2),
            impact=impact,
            description=desc,
            confidence=0.90,
            is_missing=False,
            missing_reason=None,
        )

    def evaluate_file(
        self,
        file_path: str,
        cyclomatic: int | None = None,
        maintainability_index: float | None = None,
        loc: int | None = None,
        churn_count: int | None = None,
        lines_changed: int | None = None,
        direct_dependents: int | None = None,
        transitive_dependents: int | None = None,
        coverage_pct: float | None = None,
        has_test_file: bool = False,
        defect_commit_count: int | None = None,
        associated_tests: list[str] | None = None,
        total_repo_commits: int = 10,
        graph_available: bool = True,
        tests_discovered: bool = True,
    ) -> FileRiskAssessmentRead:
        """Evaluates all five factors for a file and produces an explainable assessment."""
        factors: list[RiskFactorRead] = [
            self.evaluate_complexity_factor(cyclomatic, maintainability_index, loc),
            self.evaluate_churn_factor(churn_count, lines_changed, total_repo_commits),
            self.evaluate_blast_radius_factor(direct_dependents, transitive_dependents, graph_available),
            self.evaluate_coverage_gap_factor(coverage_pct, has_test_file, tests_discovered),
            self.evaluate_defect_history_factor(defect_commit_count),
        ]

        total_weighted_score = sum(f.weighted_score for f in factors)
        risk_score = int(round(max(0.0, min(100.0, total_weighted_score))))

        # Weighted confidence
        confidence = sum(f.confidence * f.weight for f in factors)
        confidence = round(max(0.1, min(1.0, confidence)), 3)

        missing_reasons = [f.missing_reason for f in factors if f.is_missing and f.missing_reason]
        has_missing_data = len(missing_reasons) > 0

        return FileRiskAssessmentRead(
            file_path=file_path,
            risk_score=risk_score,
            risk_tier=compute_risk_tier(risk_score),
            confidence=confidence,
            has_missing_data=has_missing_data,
            missing_reasons=missing_reasons,
            factors=factors,
            direct_dependents_count=direct_dependents or 0,
            transitive_dependents_count=transitive_dependents or (direct_dependents or 0),
            churn_count=churn_count or 0,
            lines_changed=lines_changed or 0,
            cyclomatic_complexity=cyclomatic,
            maintainability_index=maintainability_index,
            coverage_pct=coverage_pct,
            has_test_file=has_test_file,
            defect_commit_count=defect_commit_count or 0,
            associated_tests=associated_tests or [],
        )

    def evaluate_repository(
        self,
        assessment_id: str,
        repository_id: str,
        commit_sha: str,
        branch: str,
        file_assessments: list[FileRiskAssessmentRead],
    ) -> RiskAssessmentSummaryRead:
        """Aggregates file assessments into an explainable repository-level risk score."""
        if not file_assessments:
            return RiskAssessmentSummaryRead(
                id=assessment_id,
                repository_id=repository_id,
                commit_sha=commit_sha,
                branch=branch,
                model_version=self.config.version,
                model_type=self.config.model_type,
                overall_score=0,
                risk_tier="low",
                confidence=1.0,
                has_missing_data=False,
                feature_weights=self.config.as_weights_dict(),
                summary_stats={
                    "files_analyzed": 0,
                    "high_risk_count": 0,
                    "critical_risk_count": 0,
                    "missing_data_count": 0,
                    "avg_score": 0,
                },
                evaluated_at=datetime.utcnow(),
                files=[],
            )

        # Sort files descending by risk score
        sorted_files = sorted(file_assessments, key=lambda f: f.risk_score, reverse=True)

        # Composite score weighting: 70% hotspot risk, 30% median risk
        top_k = max(1, min(5, len(sorted_files) // 10 or 1))
        top_files = sorted_files[:top_k]
        top_avg = sum(f.risk_score for f in top_files) / len(top_files)

        median_idx = len(sorted_files) // 2
        median_score = sorted_files[median_idx].risk_score

        overall_score = int(round(0.70 * top_avg + 0.30 * median_score))
        overall_score = max(0, min(100, overall_score))

        avg_conf = sum(f.confidence for f in sorted_files) / len(sorted_files)
        any_missing = any(f.has_missing_data for f in sorted_files)

        high_count = sum(1 for f in sorted_files if f.risk_tier == "high")
        critical_count = sum(1 for f in sorted_files if f.risk_tier == "critical")
        missing_count = sum(1 for f in sorted_files if f.has_missing_data)

        summary_stats = {
            "files_analyzed": len(sorted_files),
            "high_risk_count": high_count,
            "critical_risk_count": critical_count,
            "missing_data_count": missing_count,
            "avg_score": round(sum(f.risk_score for f in sorted_files) / len(sorted_files), 1),
            "top_risk_file": sorted_files[0].file_path if sorted_files else None,
            "top_risk_score": sorted_files[0].risk_score if sorted_files else 0,
        }

        return RiskAssessmentSummaryRead(
            id=assessment_id,
            repository_id=repository_id,
            commit_sha=commit_sha,
            branch=branch,
            model_version=self.config.version,
            model_type=self.config.model_type,
            overall_score=overall_score,
            risk_tier=compute_risk_tier(overall_score),
            confidence=round(avg_conf, 3),
            has_missing_data=any_missing,
            feature_weights=self.config.as_weights_dict(),
            summary_stats=summary_stats,
            evaluated_at=datetime.utcnow(),
            files=sorted_files,
        )
