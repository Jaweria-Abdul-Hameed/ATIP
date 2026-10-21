"""Tests for Server-Sent Events (SSE) streaming progress endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sse_analysis_stream(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analyses/ana_test_101/events")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    assert "event: analysis_progress" in body
    assert "id: evt_ana_test_101_" in body
    assert "progress_pct" in body
    assert "data: " in body
