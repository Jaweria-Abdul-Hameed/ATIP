"""Tests for health and readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_endpoint(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["data"]["status"] == "ok"
    assert "version" in data["data"]
    assert "request_id" in data["meta"]


@pytest.mark.asyncio
async def test_readyz_endpoint(client: AsyncClient) -> None:
    response = await client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "ready"
    assert data["data"]["database"] == "connected"
