"""Risk intelligence and change-impact assessment router."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from atip_api.core.responses import DataResponse

router = APIRouter(tags=["Risk Intelligence"])


class RiskFactor(BaseModel):
    name: str = Field(..., example="Churn & Blast Radius")
    impact: str = Field(..., example="high")
    description: str = Field(
        ..., example="Modified core authentication handler imported by 14 files"
    )


class RiskyFileAssessment(BaseModel):
    file_path: str = Field(..., example="src/auth/session.ts")
    risk_score: int = Field(..., ge=0, le=100, example=87)
    severity: str = Field(..., example="critical")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.94)
    factors: list[RiskFactor] = Field(default_factory=list)
    has_missing_data: bool = Field(default=False)


class RepositoryRiskSummary(BaseModel):
    repository_id: str
    overall_score: int = Field(default=68)
    risk_tier: str = Field(default="medium")
    evaluated_commit: str = Field(default="7960a5e8")
    files: list[RiskyFileAssessment] = Field(default_factory=list)


@router.get("/repositories/{id}/risks", response_model=DataResponse[RepositoryRiskSummary])
async def get_repository_risks(id: str) -> DataResponse[RepositoryRiskSummary]:
    """Get versioned explainable risk score and ranked files for repository."""
    summary = RepositoryRiskSummary(
        repository_id=id,
        overall_score=42,
        risk_tier="medium",
        evaluated_commit="HEAD",
        files=[],
    )
    return DataResponse(data=summary)
