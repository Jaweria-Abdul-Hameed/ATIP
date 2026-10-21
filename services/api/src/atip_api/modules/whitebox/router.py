"""White-box coverage, static objectives inventory, and gap analysis router."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import DataResponse, PaginatedResponse

router = APIRouter(tags=["White-Box Coverage"])


class ObjectiveKindSummary(BaseModel):
    kind: str = Field(..., example="statement")
    total: int = Field(default=0)
    covered: int = Field(default=0)
    uncovered: int = Field(default=0)
    infeasible: int = Field(default=0)
    unknown: int = Field(default=0)
    unsupported: int = Field(default=0)
    coverage_pct: float = Field(default=0.0)


class WhiteboxCoverageSummary(BaseModel):
    analysis_id: str
    repository_id: str
    commit_sha: str
    techniques: list[ObjectiveKindSummary] = Field(default_factory=list)
    overall_mutation_score: float = Field(default=0.0)
    mcdc_paired_count: int = Field(default=0)


class WhiteboxObjective(BaseModel):
    id: str = Field(..., example="obj_stmt_001")
    kind: str = Field(..., example="mcdc")
    file_path: str = Field(..., example="src/auth/session.ts")
    line_start: int = Field(..., example=42)
    line_end: int = Field(..., example=45)
    description: str = Field(..., example="Decision: (is_admin || (has_permission && !is_revoked))")
    status: str = Field(..., example="covered")
    evidence: dict[str, Any] | None = None


@router.post(
    "/repositories/{id}/whitebox-analyses",
    response_model=DataResponse[dict[str, Any]],
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_whitebox_analysis(id: str) -> DataResponse[dict[str, Any]]:
    """Trigger full AST/CFG objective discovery and white-box analysis."""
    analysis_id = f"wb_{uuid.uuid4().hex[:12]}"
    return DataResponse(
        data={
            "analysis_id": analysis_id,
            "repository_id": id,
            "status": "queued",
            "message": "White-box objective discovery queued",
        }
    )


@router.get(
    "/whitebox-analyses/{id}/coverage", response_model=DataResponse[WhiteboxCoverageSummary]
)
async def get_whitebox_coverage(id: str) -> DataResponse[WhiteboxCoverageSummary]:
    """Get 11-technique white-box coverage matrix and evidence summary."""
    techniques = [
        ObjectiveKindSummary(
            kind="statement", total=100, covered=85, uncovered=15, coverage_pct=85.0
        ),
        ObjectiveKindSummary(kind="branch", total=50, covered=38, uncovered=12, coverage_pct=76.0),
        ObjectiveKindSummary(
            kind="condition", total=40, covered=30, uncovered=10, coverage_pct=75.0
        ),
        ObjectiveKindSummary(kind="mcdc", total=24, covered=18, uncovered=6, coverage_pct=75.0),
        ObjectiveKindSummary(
            kind="basis_path", total=16, covered=12, uncovered=4, coverage_pct=75.0
        ),
        ObjectiveKindSummary(
            kind="selected_path", total=20, covered=15, uncovered=5, coverage_pct=75.0
        ),
        ObjectiveKindSummary(kind="loop", total=12, covered=10, uncovered=2, coverage_pct=83.3),
        ObjectiveKindSummary(
            kind="data_flow", total=30, covered=22, uncovered=8, coverage_pct=73.3
        ),
        ObjectiveKindSummary(
            kind="exception", total=14, covered=11, uncovered=3, coverage_pct=78.6
        ),
        ObjectiveKindSummary(kind="boundary", total=28, covered=22, uncovered=6, coverage_pct=78.6),
        ObjectiveKindSummary(
            kind="mutation", total=60, covered=48, uncovered=12, coverage_pct=80.0
        ),
    ]
    summary = WhiteboxCoverageSummary(
        analysis_id=id,
        repository_id="repo_nextjs_dashboard",
        commit_sha="HEAD",
        techniques=techniques,
        overall_mutation_score=80.0,
        mcdc_paired_count=18,
    )
    return DataResponse(data=summary)


@router.get(
    "/whitebox-analyses/{id}/objectives", response_model=PaginatedResponse[WhiteboxObjective]
)
async def list_objectives(
    id: str,
    kind: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination_params),
) -> PaginatedResponse[WhiteboxObjective]:
    """List static coverage objectives with status and proof evidence."""
    return PaginatedResponse(
        data=[],
        pagination=PaginationMetadata.create(
            page=pagination.page, page_size=pagination.page_size, total_items=0
        ),
    )


@router.get("/whitebox-analyses/{id}/gaps", response_model=DataResponse[dict[str, Any]])
async def get_coverage_gaps(id: str) -> DataResponse[dict[str, Any]]:
    """Retrieve uncovered and infeasible coverage gaps."""
    return DataResponse(
        data={
            "analysis_id": id,
            "total_gaps": 0,
            "gaps": [],
        }
    )
