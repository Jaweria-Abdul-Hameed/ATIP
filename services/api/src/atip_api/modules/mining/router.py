"""Repository mining, commit history, and analysis progress SSE router."""

import asyncio
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from atip_api.core.responses import DataResponse
from atip_api.core.sse import ServerSentEvent, sse_event_stream

router = APIRouter(tags=["Mining & Analysis"])


class AnalysisTriggerRequest(BaseModel):
    commit_sha: str | None = Field(default=None, example="7960a5e8")
    branch: str | None = Field(default="main", example="main")


class AnalysisJobRead(BaseModel):
    id: str
    repository_id: str
    status: str = Field(default="running")
    progress_pct: int = Field(default=0)
    current_step: str = Field(default="Initializing repository checkout")
    commit_sha: str = Field(default="HEAD")


@router.post(
    "/repositories/{id}/analyses",
    response_model=DataResponse[AnalysisJobRead],
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_analysis(
    id: str, payload: AnalysisTriggerRequest
) -> DataResponse[AnalysisJobRead]:
    """Trigger repository mining and static analysis job."""
    job_id = f"job_ana_{uuid.uuid4().hex[:12]}"
    job = AnalysisJobRead(
        id=job_id,
        repository_id=id,
        status="queued",
        progress_pct=0,
        current_step="Queued for analysis worker",
        commit_sha=payload.commit_sha or "HEAD",
    )
    return DataResponse(data=job)


@router.get("/analyses/{id}", response_model=DataResponse[AnalysisJobRead])
async def get_analysis(id: str) -> DataResponse[AnalysisJobRead]:
    """Get analysis job status and progress."""
    job = AnalysisJobRead(
        id=id,
        repository_id="repo_nextjs_dashboard",
        status="completed",
        progress_pct=100,
        current_step="Analysis completed successfully",
        commit_sha="HEAD",
    )
    return DataResponse(data=job)


@router.get("/analyses/{id}/events")
async def stream_analysis_events(id: str, request: Request) -> StreamingResponse:
    """Stream real-time analysis progress events via Server-Sent Events (SSE)."""

    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        steps = [
            ("queued", 0, "Job queued in outbox worker"),
            ("provisioning", 20, "Extracting commit diff and file changes"),
            ("running", 50, "Building dependency and import graph"),
            ("running", 80, "Discovering whitebox coverage objectives"),
            ("completed", 100, "Analysis complete. Persisted artifacts to object store"),
        ]
        for step_idx, (job_status, pct, desc) in enumerate(steps):
            if await request.is_disconnected():
                break
            yield ServerSentEvent(
                id=f"evt_{id}_{step_idx}",
                event="analysis_progress",
                data={
                    "job_id": id,
                    "status": job_status,
                    "progress_pct": pct,
                    "current_step": desc,
                },
            )
            await asyncio.sleep(0.01)

    return StreamingResponse(
        sse_event_stream(event_generator()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
