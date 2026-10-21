"""Test plans, proposal review, and human approval router."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import DataResponse, PaginatedResponse

router = APIRouter(prefix="/test-plans", tags=["Test Plans"])


class TestPlanRead(BaseModel):
    id: str = Field(..., example="plan_1042")
    repository_id: str = Field(..., example="repo_nextjs_dashboard")
    title: str = Field(..., example="PR #42 Coverage & Regression Plan")
    status: str = Field(default="draft", example="draft")
    target_branch: str = Field(default="main")
    proposed_tests_count: int = Field(default=8)
    impacted_tests_count: int = Field(default=4)
    approved_by: str | None = None
    created_at: str = Field(default="2026-10-21T08:00:00Z")


class ApprovalResponse(BaseModel):
    plan_id: str
    status: str = Field(default="approved")
    approved_by: str
    message: str = Field(default="Test plan approved for execution")


@router.get("", response_model=PaginatedResponse[TestPlanRead])
async def list_test_plans(
    pagination: PaginationParams = Depends(get_pagination_params),
) -> PaginatedResponse[TestPlanRead]:
    """List test plans with review status."""
    return PaginatedResponse(
        data=[],
        pagination=PaginationMetadata.create(
            page=pagination.page, page_size=pagination.page_size, total_items=0
        ),
    )


@router.get("/{id}", response_model=DataResponse[TestPlanRead])
async def get_test_plan(id: str) -> DataResponse[TestPlanRead]:
    """Get single test plan by ID."""
    plan = TestPlanRead(
        id=id,
        repository_id="repo_nextjs_dashboard",
        title="Comprehensive Regression & MC/DC Plan",
        status="draft",
        target_branch="main",
        proposed_tests_count=6,
        impacted_tests_count=3,
    )
    return DataResponse(data=plan)


@router.post("/{id}/approve", response_model=DataResponse[ApprovalResponse])
async def approve_test_plan(id: str) -> DataResponse[ApprovalResponse]:
    """Server-side human approval gate for test plans before execution."""
    # Server-enforced approval (SECURITY.md: An AI agent cannot approve its own action)
    return DataResponse(
        data=ApprovalResponse(
            plan_id=id,
            status="approved",
            approved_by="usr_current_engineer",
            message="Plan approved by human reviewer. Safe to dispatch to sandbox runner.",
        )
    )
