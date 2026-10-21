"""Audit logging and tenant compliance event trail router."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from atip_api.core.pagination import PaginationMetadata, PaginationParams, get_pagination_params
from atip_api.core.responses import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


class AuditEventRead(BaseModel):
    id: str = Field(..., example="aud_101")
    user_id: str | None = Field(default=None)
    action: str = Field(..., example="plan.approve")
    target_type: str = Field(..., example="test_plan")
    target_id: str = Field(..., example="plan_1042")
    payload: dict[str, Any] | None = None
    created_at: str = Field(default="2026-10-21T08:30:00Z")


@router.get("/events", response_model=PaginatedResponse[AuditEventRead])
async def list_audit_events(
    pagination: PaginationParams = Depends(get_pagination_params),
) -> PaginatedResponse[AuditEventRead]:
    """Retrieve tenant audit log events."""
    return PaginatedResponse(
        data=[],
        pagination=PaginationMetadata.create(
            page=pagination.page, page_size=pagination.page_size, total_items=0
        ),
    )
