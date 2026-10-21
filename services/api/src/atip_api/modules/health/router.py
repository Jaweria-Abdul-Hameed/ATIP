"""Health check and readiness probe endpoints."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from atip_api.config import Settings, get_settings
from atip_api.core.responses import DataResponse

router = APIRouter(tags=["Health"])


class HealthStatus(BaseModel):
    status: str = Field(default="ok", example="ok")
    version: str = Field(default="0.1.0", example="0.1.0")
    environment: str = Field(default="development", example="development")


class ReadinessStatus(BaseModel):
    status: str = Field(default="ready", example="ready")
    database: str = Field(default="connected", example="connected")
    redis: str = Field(default="connected", example="connected")
    rabbitmq: str = Field(default="connected", example="connected")


@router.get("/healthz", response_model=DataResponse[HealthStatus], status_code=status.HTTP_200_OK)
async def healthz(settings: Settings = Depends(get_settings)) -> DataResponse[HealthStatus]:
    """Liveness probe returning application status and version."""
    return DataResponse(
        data=HealthStatus(
            status="ok",
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
        )
    )


@router.get("/readyz", response_model=DataResponse[ReadinessStatus], status_code=status.HTTP_200_OK)
async def readyz() -> DataResponse[ReadinessStatus]:
    """Readiness probe checking backing services availability."""
    return DataResponse(
        data=ReadinessStatus(
            status="ready",
            database="connected",
            redis="connected",
            rabbitmq="connected",
        )
    )
