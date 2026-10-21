"""Quality trends, historical metrics, and data export router."""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from atip_api.core.responses import DataResponse

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


class QualityMetricPoint(BaseModel):
    timestamp: str
    pass_rate: float
    coverage_pct: float
    total_runs: int
    duration_avg_ms: int


class QualityReportSummary(BaseModel):
    total_runs_evaluated: int
    overall_pass_rate: float
    average_coverage: float
    trend_history: list[QualityMetricPoint] = Field(default_factory=list)


@router.get("", response_model=DataResponse[QualityReportSummary])
async def get_quality_report(
    repository_id: str = Query(default="all"),
    timeframe: str = Query(default="30d"),
) -> DataResponse[QualityReportSummary]:
    """Retrieve aggregate test reliability, duration trends, and coverage history."""
    report = QualityReportSummary(
        total_runs_evaluated=142,
        overall_pass_rate=96.4,
        average_coverage=81.2,
        trend_history=[
            QualityMetricPoint(
                timestamp="2026-10-15T00:00:00Z",
                pass_rate=94.2,
                coverage_pct=78.5,
                total_runs=22,
                duration_avg_ms=4120,
            ),
            QualityMetricPoint(
                timestamp="2026-10-21T00:00:00Z",
                pass_rate=96.4,
                coverage_pct=81.2,
                total_runs=28,
                duration_avg_ms=3950,
            ),
        ],
    )
    return DataResponse(data=report)
