"""Tests for core API v1 endpoints and contracts."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == "developer@atip.dev"
    assert len(data["data"]["organizations"]) > 0


@pytest.mark.asyncio
async def test_create_and_list_organization(client: AsyncClient) -> None:
    # Create org
    create_res = await client.post(
        "/api/v1/organizations",
        json={"name": "Acme Test Org", "slug": "acme-test-org"},
    )
    assert create_res.status_code == 201
    org = create_res.json()["data"]
    assert org["slug"] == "acme-test-org"
    assert org["name"] == "Acme Test Org"
    org_id = org["id"]

    # Get org by ID
    get_res = await client.get(f"/api/v1/organizations/{org_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == org_id

    # List orgs
    list_res = await client.get("/api/v1/organizations")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "data" in list_data
    assert "pagination" in list_data
    assert any(o["id"] == org_id for o in list_data["data"])


@pytest.mark.asyncio
async def test_whitebox_coverage_summary(client: AsyncClient) -> None:
    response = await client.get("/api/v1/whitebox-analyses/wb_test_101/coverage")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_id"] == "wb_test_101"
    # All 11 techniques present
    assert len(data["techniques"]) == 11
    kinds = [t["kind"] for t in data["techniques"]]
    assert "statement" in kinds
    assert "branch" in kinds
    assert "condition" in kinds
    assert "mcdc" in kinds
    assert "mutation" in kinds


@pytest.mark.asyncio
async def test_test_plan_approval_gate(client: AsyncClient) -> None:
    # Server-side human approval
    response = await client.post("/api/v1/test-plans/plan_1042/approve")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "approved"
    assert data["approved_by"] == "usr_current_engineer"


@pytest.mark.asyncio
async def test_triage_failure_with_citations(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/analysis/triage",
        json={
            "run_id": "run_1042",
            "failed_test_name": "test_auth_token_revocation",
            "stack_trace": "AssertionError: token is still valid after logout",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "hypothesis" in data
    assert data["is_confirmed_fact"] is False
    assert data["requires_human_approval"] is True
    assert len(data["citations"]) > 0
