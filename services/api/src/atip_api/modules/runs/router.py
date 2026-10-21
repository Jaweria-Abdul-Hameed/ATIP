"""Test runs and sandbox execution job management router."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import DataResponse, PaginatedResponse

router = APIRouter(tags=["Test Runs & Execution"])


class TestRunRead(BaseModel):
    id: str = Field(..., example="run_1042")
    repository_id: str = Field(..., example="repo_nextjs_dashboard")
    plan_id: str | None = Field(default=None, example="plan_1042")
    status: str = Field(default="completed", example="completed")
    commit_sha: str = Field(default="7960a5e8")
    branch: str = Field(default="main")
    duration_ms: int = Field(default=4320)
    passed_count: int = Field(default=28)
    failed_count: int = Field(default=1)
    flaky_count: int = Field(default=0)
    created_at: str = Field(default="2026-10-21T08:15:00Z")


class JobCancelResponse(BaseModel):
    job_id: str
    status: str = Field(default="cancelled")
    message: str = Field(default="Execution job cancelled successfully")


@router.get("/test-runs", response_model=PaginatedResponse[TestRunRead])
async def list_test_runs(
    pagination: PaginationParams = Depends(get_pagination_params),
) -> PaginatedResponse[TestRunRead]:
    """List execution test runs."""
    return PaginatedResponse(
        data=[],
        pagination=PaginationMetadata.create(
            page=pagination.page, page_size=pagination.page_size, total_items=0
        ),
    )


@router.get("/test-runs/{id}", response_model=DataResponse[TestRunRead])
async def get_test_run(id: str) -> DataResponse[TestRunRead]:
    """Get single test run details."""
    run = TestRunRead(
        id=id,
        repository_id="repo_nextjs_dashboard",
        plan_id="plan_1042",
        status="completed",
        commit_sha="7960a5e8",
        branch="main",
        duration_ms=4320,
        passed_count=28,
        failed_count=1,
    )
    return DataResponse(data=run)


@router.post("/execution-jobs/{id}/cancel", response_model=DataResponse[JobCancelResponse])
async def cancel_execution_job(id: str) -> DataResponse[JobCancelResponse]:
    """Cancel in-flight execution job and release sandbox resources."""
    return DataResponse(
        data=JobCancelResponse(
            job_id=id,
            status="cancelled",
            message="Execution job cancelled and sandbox worker stopped",
        )
    )
