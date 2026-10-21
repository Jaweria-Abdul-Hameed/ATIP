"""Tests for OIDC authentication, session tokens, protected routes, and session expiry."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.organization import (
    User,
)
from atip_api.modules.identity.session import create_session_token


@pytest.mark.asyncio
async def test_oidc_login_generates_auth_url(client: AsyncClient) -> None:
    """Test login endpoint generates OIDC URL with CSRF state token."""
    response = await client.get("/api/v1/auth/login")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "authorization_url" in data
    assert "state" in data
    assert "client_id=" in data["authorization_url"]
    assert f"state={data['state']}" in data["authorization_url"]


@pytest.mark.asyncio
async def test_oidc_callback_rejects_invalid_state(client: AsyncClient) -> None:
    """Test callback rejects invalid or missing state (CSRF defense)."""
    response = await client.post(
        "/api/v1/auth/callback",
        json={"code": "mock_code_test", "state": "tampered_nonexistent_state"},
    )
    assert response.status_code == 400
    err = response.json()["error"]
    assert err["code"] == "INVALID_OIDC_STATE"


@pytest.mark.asyncio
async def test_oidc_callback_and_session_creation(client: AsyncClient) -> None:
    """Test successful OIDC callback creates user, workspace, and issues session cookie."""
    # Step 1: initiate login to obtain valid state
    login_res = await client.get("/api/v1/auth/login")
    state = login_res.json()["data"]["state"]

    # Step 2: exchange callback code
    callback_res = await client.post(
        "/api/v1/auth/callback",
        json={"code": "mock_code_alice", "state": state},
    )
    assert callback_res.status_code == 200
    data = callback_res.json()["data"]
    assert data["authenticated"] is True
    assert data["user"]["email"] == "alice@atip.dev"
    assert data["user"]["name"] == "ATIP Alice"
    assert len(data["user"]["organizations"]) == 1
    assert data["user"]["organizations"][0]["role"] == "owner"
    assert data["token"] is not None

    # Verify session cookie was set
    assert "atip_session" in callback_res.cookies

    # Step 3: Call protected route /api/v1/me using session cookie
    me_res = await client.get("/api/v1/me")
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["email"] == "alice@atip.dev"
    assert me_data["name"] == "ATIP Alice"


@pytest.mark.asyncio
async def test_protected_route_rejects_unauthenticated_requests(client: AsyncClient) -> None:
    """Test protected /api/v1/me returns 401 UNAUTHENTICATED when no token is provided."""
    response = await client.get("/api/v1/me")
    assert response.status_code == 401
    err = response.json()["error"]
    assert err["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_session_expiry_handling(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that expired session tokens return 401 SESSION_EXPIRED."""
    # Create test user
    user = User(
        email="bob@atip.dev",
        name="Bob Architect",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Generate token already expired in the past
    expired_token, _ = create_session_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )

    # Attempt to access /api/v1/me with expired token in Authorization header
    response = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    err = response.json()["error"]
    assert err["code"] == "SESSION_EXPIRED"
    assert "expired" in err["message"].lower()


@pytest.mark.asyncio
async def test_logout_and_revocation(client: AsyncClient) -> None:
    """Test logout invalidates the session token and clears the cookie."""
    # Login
    login_res = await client.get("/api/v1/auth/login")
    state = login_res.json()["data"]["state"]

    callback_res = await client.post(
        "/api/v1/auth/callback",
        json={"code": "mock_code_charlie", "state": state},
    )
    token = callback_res.json()["data"]["token"]

    # Verify session is valid
    me_res = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200

    # Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["success"] is True

    # Attempting to use revoked token should now fail with 401 UNAUTHENTICATED
    revoked_res = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoked_res.status_code == 401
    assert revoked_res.json()["error"]["code"] == "UNAUTHENTICATED"
