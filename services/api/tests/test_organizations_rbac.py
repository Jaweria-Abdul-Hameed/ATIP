"""Tests for organization creation, membership, invitations, tenant isolation, and RBAC."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models.organization import (
    User,
)
from atip_api.modules.identity.session import create_session_token


async def _create_test_user_and_token(db: AsyncSession, email: str, name: str) -> tuple[User, str]:
    user = User(email=email, name=name, is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token, _ = create_session_token(user_id=user.id, email=user.email, name=user.name)
    return user, token


@pytest.mark.asyncio
async def test_create_organization_assigns_owner(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test creating an organization assigns the creator as Owner."""
    user, token = await _create_test_user_and_token(db_session, "creator@atip.dev", "Creator User")

    response = await client.post(
        "/api/v1/organizations",
        json={"name": "Alpha Corp", "slug": "alpha-corp"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Alpha Corp"
    assert data["slug"] == "alpha-corp"
    assert data["role"] == "owner"


@pytest.mark.asyncio
async def test_create_organization_slug_conflict(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test creating an organization with duplicate slug returns 409 Conflict."""
    _, token = await _create_test_user_and_token(db_session, "u1@atip.dev", "U1")

    # Create first org
    res1 = await client.post(
        "/api/v1/organizations",
        json={"name": "Beta Corp", "slug": "beta-corp"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201

    # Attempt duplicate slug
    res2 = await client.post(
        "/api/v1/organizations",
        json={"name": "Beta Duplicate", "slug": "beta-corp"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_organization_membership_and_rbac_flow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """End-to-end test of member invitation, role verification, and RBAC permission checks."""
    # 1. Create owner and developer users
    owner, owner_token = await _create_test_user_and_token(
        db_session, "owner@atip.dev", "Alice Owner"
    )
    dev, dev_token = await _create_test_user_and_token(
        db_session, "developer@atip.dev", "Dave Developer"
    )
    viewer, viewer_token = await _create_test_user_and_token(
        db_session, "viewer@atip.dev", "Vera Viewer"
    )

    # 2. Owner creates organization
    org_res = await client.post(
        "/api/v1/organizations",
        json={"name": "Stark Industries", "slug": "stark-industries"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["data"]["id"]

    # 3. Developer attempts to invite someone (should fail with 403 Forbidden)
    dev_invite_res = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "external@atip.dev", "role": "developer"},
        headers={"Authorization": f"Bearer {dev_token}"},
    )
    # dev is not in org -> 403 TENANT_MISMATCH
    assert dev_invite_res.status_code == 403

    # 4. Owner invites Developer
    invite_res = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": dev.email, "role": "developer"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert invite_res.status_code == 201
    invite_data = invite_res.json()["data"]
    inv_token = invite_data["token"]
    assert invite_data["role"] == "developer"

    # 5. Developer accepts invitation
    accept_res = await client.post(
        f"/api/v1/invitations/{inv_token}/accept",
        headers={"Authorization": f"Bearer {dev_token}"},
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["data"]["success"] is True

    # Re-accepting should fail with 409 Conflict
    reaccept_res = await client.post(
        f"/api/v1/invitations/{inv_token}/accept",
        headers={"Authorization": f"Bearer {dev_token}"},
    )
    assert reaccept_res.status_code == 409

    # 6. List members (both Owner and Developer now visible)
    members_res = await client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers={"Authorization": f"Bearer {dev_token}"},
    )
    assert members_res.status_code == 200
    members = members_res.json()["data"]
    assert len(members) == 2
    roles = {m["email"]: m["role"] for m in members}
    assert roles["owner@atip.dev"] == "owner"
    assert roles["developer@atip.dev"] == "developer"

    # 7. Developer (role developer) attempts to update members -> 403 FORBIDDEN
    dev_update_res = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{dev.id}",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {dev_token}"},
    )
    assert dev_update_res.status_code == 403
    assert dev_update_res.json()["error"]["code"] == "FORBIDDEN"

    # 8. Owner promotes Developer to Maintainer
    owner_update_res = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{dev.id}",
        json={"role": "maintainer"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_update_res.status_code == 200
    assert owner_update_res.json()["data"]["role"] == "maintainer"

    # 9. Owner tries to demote themselves when they are the only Owner -> 422 validation error
    owner_demote_self = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{owner.id}",
        json={"role": "developer"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_demote_self.status_code == 422
    assert "last remaining Owner" in owner_demote_self.json()["error"]["message"]


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that users cannot access resources belonging to organizations they are not members of."""
    # Org A
    user_a, token_a = await _create_test_user_and_token(db_session, "user_a@atip.dev", "User A")
    res_a = await client.post(
        "/api/v1/organizations",
        json={"name": "Tenant A", "slug": "tenant-a"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    org_a_id = res_a.json()["data"]["id"]

    # Org B
    user_b, token_b = await _create_test_user_and_token(db_session, "user_b@atip.dev", "User B")
    res_b = await client.post(
        "/api/v1/organizations",
        json={"name": "Tenant B", "slug": "tenant-b"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.json()["data"]["id"] is not None

    # User B attempts to access Org A's members
    cross_access = await client.get(
        f"/api/v1/organizations/{org_a_id}/members",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert cross_access.status_code == 403
    err = cross_access.json()["error"]
    assert err["code"] == "TENANT_MISMATCH"
