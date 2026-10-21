"""Comprehensive security, tenant crossover, RBAC hierarchy, and webhook forgery test suite for M2."""

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.config import get_settings
from atip_api.db.models import Organization, OrganizationMembership, Repository, User
from atip_api.db.models.organization import MembershipRole
from atip_api.modules.identity.session import create_session_token


async def _create_tenant_with_user(
    db: AsyncSession,
    email: str,
    name: str,
    org_slug: str,
    role: MembershipRole,
    is_user_active: bool = True,
    is_org_active: bool = True,
) -> tuple[User, Organization, str]:
    user = User(email=email, name=name, is_active=is_user_active)
    db.add(user)
    await db.flush()

    org = Organization(name=f"{name}'s Org", slug=org_slug, is_active=is_org_active)
    db.add(org)
    await db.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=role,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(user)
    await db.refresh(org)

    token, _ = create_session_token(
        user_id=user.id, email=user.email, name=user.name, org_ids=[org.id]
    )
    return user, org, token


@pytest.mark.asyncio
async def test_rbac_full_hierarchy_enforcement(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verify RBAC role hierarchy: Owner > Admin > Maintainer > Developer > Viewer."""
    # Create an organization with Owner
    owner, org, owner_token = await _create_tenant_with_user(
        db_session, "superowner@atip.dev", "Super Owner", "hierarchy-corp", MembershipRole.OWNER
    )

    # Helper to add additional user to this org
    async def add_member(email: str, name: str, role: MembershipRole) -> tuple[User, str]:
        u = User(email=email, name=name, is_active=True)
        db_session.add(u)
        await db_session.flush()
        m = OrganizationMembership(organization_id=org.id, user_id=u.id, role=role)
        db_session.add(m)
        await db_session.commit()
        await db_session.refresh(u)
        tok, _ = create_session_token(u.id, u.email, u.name, [org.id])
        return u, tok

    admin_user, admin_token = await add_member("adm@atip.dev", "Admin", MembershipRole.ADMIN)
    maint_user, maint_token = await add_member("maint@atip.dev", "Maint", MembershipRole.MAINTAINER)
    dev_user, dev_token = await add_member("dev1@atip.dev", "Dev", MembershipRole.DEVELOPER)
    viewer_user, viewer_token = await add_member("view1@atip.dev", "Viewer", MembershipRole.VIEWER)

    # 1. Admin can invite member
    res_adm_invite = await client.post(
        f"/api/v1/organizations/{org.id}/invitations",
        json={"email": "newbie@atip.dev", "role": "developer"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org.id},
    )
    assert res_adm_invite.status_code == 201

    # 2. Maintainer CANNOT invite member (requires Admin+)
    res_maint_invite = await client.post(
        f"/api/v1/organizations/{org.id}/invitations",
        json={"email": "newbie2@atip.dev", "role": "developer"},
        headers={"Authorization": f"Bearer {maint_token}", "X-Organization-ID": org.id},
    )
    assert res_maint_invite.status_code == 403
    assert res_maint_invite.json()["error"]["code"] == "FORBIDDEN"

    # 3. Developer CANNOT invite member
    res_dev_invite = await client.post(
        f"/api/v1/organizations/{org.id}/invitations",
        json={"email": "newbie3@atip.dev", "role": "developer"},
        headers={"Authorization": f"Bearer {dev_token}", "X-Organization-ID": org.id},
    )
    assert res_dev_invite.status_code == 403

    # 4. Viewer CANNOT invite member
    res_view_invite = await client.post(
        f"/api/v1/organizations/{org.id}/invitations",
        json={"email": "newbie4@atip.dev", "role": "developer"},
        headers={"Authorization": f"Bearer {viewer_token}", "X-Organization-ID": org.id},
    )
    assert res_view_invite.status_code == 403

    # 5. Admin CANNOT demote or modify Owner
    res_admin_demote_owner = await client.patch(
        f"/api/v1/organizations/{org.id}/members/{owner.id}",
        json={"role": "developer"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Organization-ID": org.id},
    )
    assert res_admin_demote_owner.status_code == 403
    assert "Only an Owner" in res_admin_demote_owner.json()["error"]["message"]


@pytest.mark.asyncio
async def test_cross_tenant_strict_boundary(client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify tenant isolation: Tenant A user cannot access or modify Tenant B data."""
    # Tenant Alpha
    _, org_alpha, token_alpha = await _create_tenant_with_user(
        db_session, "alpha@atip.dev", "Alpha User", "tenant-alpha", MembershipRole.OWNER
    )
    repo_alpha = Repository(
        organization_id=org_alpha.id,
        github_repo_id=909001,
        name="alpha-repo",
        full_name="tenant-alpha/alpha-repo",
        default_branch="main",
        clone_url="https://github.com/tenant-alpha/alpha-repo.git",
    )
    db_session.add(repo_alpha)
    await db_session.commit()

    # Tenant Beta
    _, org_beta, token_beta = await _create_tenant_with_user(
        db_session, "beta@atip.dev", "Beta User", "tenant-beta", MembershipRole.OWNER
    )

    # Beta attempts to read Alpha's repository via API
    res = await client.get(
        f"/api/v1/repositories/{repo_alpha.id}",
        headers={"Authorization": f"Bearer {token_beta}", "X-Organization-ID": org_beta.id},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"

    # Beta attempts to access Alpha's members
    res_members = await client.get(
        f"/api/v1/organizations/{org_alpha.id}/members",
        headers={"Authorization": f"Bearer {token_beta}", "X-Organization-ID": org_alpha.id},
    )
    assert res_members.status_code == 403
    assert res_members.json()["error"]["code"] == "TENANT_MISMATCH"


@pytest.mark.asyncio
async def test_webhook_security_tamper_detection(client: AsyncClient) -> None:
    """Verify that even a 1-byte alteration in payload invalidates webhook HMAC."""
    settings = get_settings()
    legit_body = json.dumps({"action": "synchronize", "repo": "atip"}).encode("utf-8")
    sig = (
        "sha256="
        + hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), legit_body, hashlib.sha256).hexdigest()
    )

    # Tampered body with original signature
    tampered_body = json.dumps({"action": "synchronize", "repo": "atip-hacked"}).encode("utf-8")

    response = await client.post(
        "/api/v1/github/webhooks",
        content=tampered_body,
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "deliv_tamper_test_01",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "WEBHOOK_SIGNATURE_INVALID"
