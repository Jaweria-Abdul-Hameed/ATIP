"""Standardized JSON response envelopes matching ATIP architecture contracts."""

from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from atip_api.core.pagination import PaginationMetadata

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str | None = Field(default=None, description="Unique correlation ID for request")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of response generation",
    )


class DataResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    pagination: PaginationMetadata
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
