"""Tests for standardized response and error envelopes, middleware, and request IDs."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_generation(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")
    assert response.json()["meta"]["request_id"] == response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_request_id_preservation(client: AsyncClient) -> None:
    custom_id = "req_custom_trace_987654"
    response = await client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
    assert response.json()["meta"]["request_id"] == custom_id


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-Response-Time-Ms" in response.headers


@pytest.mark.asyncio
async def test_structured_error_envelope_on_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/organizations/org_nonexistent_id")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()
    assert data["error"]["request_id"] is not None


@pytest.mark.asyncio
async def test_validation_error_envelope(client: AsyncClient) -> None:
    # OrganizationCreate requires name min_length=2 and slug min_length=2
    response = await client.post("/api/v1/organizations", json={"name": "A", "slug": ""})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(data["error"]["details"], list)
    assert len(data["error"]["details"]) > 0
