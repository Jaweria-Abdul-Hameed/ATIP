"""Pydantic schemas for risk assessment, explainable factors, and impact propagation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RiskFactorRead(BaseModel):
    """Individual explainable factor contributing to file or commit risk score."""

    factor_key: str = Field(..., example="complexity")
    name: str = Field(..., example="Code Complexity & Maintainability")
    raw_value: Any = Field(default=None)
    normalized_score: float = Field(..., ge=0.0, le=100.0, example=75.0)
    weight: float = Field(..., ge=0.0, le=1.0, example=0.25)
    weighted_score: float = Field(..., ge=0.0, le=100.0, example=18.75)
    impact: str = Field(..., example="high")  # low, medium, high, critical
    description: str = Field(
        ...,
        example="Cyclomatic complexity of 24 exceeds warning threshold of 15 (MI: 48.2).",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, example=0.95)
    is_missing: bool = Field(default=False)
    missing_reason: str | None = Field(default=None)


class ChangeImpactNode(BaseModel):
    """File in the transitive dependency graph impacted by a change."""

    file_path: str
    depth: int = Field(default=0, ge=0)
    impact_score: float = Field(..., ge=0.0, le=100.0)
    is_direct: bool = Field(default=True)
    imported_by: list[str] = Field(default_factory=list)
    propagation_reason: str = Field(
        ..., example="Directly imports modified core authentication module"
    )


class FileRiskAssessmentRead(BaseModel):
    """Detailed risk assessment for a single file with explainable factors."""

    file_path: str = Field(..., example="src/auth/session.ts")
    risk_score: int = Field(..., ge=0, le=100, example=82)
    risk_tier: str = Field(..., example="high")  # low, medium, high, critical
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.92)
    has_missing_data: bool = Field(default=False)
    missing_reasons: list[str] = Field(default_factory=list)
    factors: list[RiskFactorRead] = Field(default_factory=list)

    # Core component signals
    direct_dependents_count: int = Field(default=0)
    transitive_dependents_count: int = Field(default=0)
    churn_count: int = Field(default=0)
    lines_changed: int = Field(default=0)
    cyclomatic_complexity: int | None = Field(default=None)
    maintainability_index: float | None = Field(default=None)
    coverage_pct: float | None = Field(default=None)
    has_test_file: bool = Field(default=False)
    defect_commit_count: int = Field(default=0)
    associated_tests: list[str] = Field(default_factory=list)


class RiskAssessmentSummaryRead(BaseModel):
    """Aggregated repository-level risk assessment with ranked files and provenance."""

    id: str
    repository_id: str
    commit_sha: str
    branch: str = "main"
    model_version: str = "deterministic-v1.0.0"
    model_type: str = "deterministic"
    overall_score: int = Field(..., ge=0, le=100, example=68)
    risk_tier: str = Field(..., example="medium")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.91)
    has_missing_data: bool = Field(default=False)
    feature_weights: dict[str, float] = Field(default_factory=dict)
    summary_stats: dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime
    files: list[FileRiskAssessmentRead] = Field(default_factory=list)
    impacted_nodes: list[ChangeImpactNode] = Field(default_factory=list)


class RiskEvaluateRequest(BaseModel):
    """Request payload to trigger on-demand risk evaluation."""

    commit_sha: str | None = None
    branch: str | None = "main"
    force_recompute: bool = False
