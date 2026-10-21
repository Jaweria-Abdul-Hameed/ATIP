"""Tests for GitHub App install flow, encrypted token storage, and installation-scoped credentials."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.core.crypto import decrypt_secret, encrypt_secret
from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from atip_api.db.models.repository import GitHubInstallation
from atip_api.modules.github.service import get_github_app_service
from atip_api.modules.identity.session import create_session_token


async def _create_test_user_and_org(
    db: AsyncSession,
    email: str,
    name: str,
    org_slug: str,
    role: MembershipRole = MembershipRole.ADMIN,
) -> tuple[User, Organization, str]:
    user = User(email=email, name=name, is_active=True)
    db.add(user)
    await db.flush()

    org = Organization(name=f"{name}'s Org", slug=org_slug, is_active=True)
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


def test_crypto_encryption_and_decryption() -> None:
    """Test symmetric encryption and decryption of sensitive tokens."""
    plaintext = "ghs_test_token_secret_123456789"
    ciphertext = encrypt_secret(plaintext)
    assert ciphertext != plaintext
    decrypted = decrypt_secret(ciphertext)
    assert decrypted == plaintext


@pytest.mark.asyncio
async def test_get_install_url(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test getting GitHub App install URL includes target organization in state."""
    _, org, token = await _create_test_user_and_org(
        db_session, "admin@atip.dev", "Admin User", "alpha-org", MembershipRole.ADMIN
    )

    response = await client.get(
        "/api/v1/github/install-url",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "https://github.com/apps/" in data["install_url"]
    assert f"state={org.id}" in data["install_url"]


@pytest.mark.asyncio
async def test_github_app_callback_and_encrypted_token_storage(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test callback stores installation with encrypted token in database."""
    _, org, token = await _create_test_user_and_org(
        db_session, "owner@atip.dev", "Owner User", "beta-org", MembershipRole.OWNER
    )

    # Invoke callback with installation ID and state=org.id
    response = await client.get(
        "/api/v1/github/callback?installation_id=98765432&setup_action=install&state=" + org.id,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["installation_id"] == 98765432
    assert data["organization_id"] == org.id

    # Verify directly from database that token is stored encrypted
    stmt = select(GitHubInstallation).where(GitHubInstallation.installation_id == 98765432)
    inst = (await db_session.execute(stmt)).scalar_one()
    assert inst.encrypted_token is not None
    # Token in database must NOT be plaintext
    assert not inst.encrypted_token.startswith("ghs_")
    # Decrypting returns valid plaintext token
    decrypted = decrypt_secret(inst.encrypted_token)
    assert decrypted.startswith("ghs_inst_98765432")


@pytest.mark.asyncio
async def test_get_installation_token_and_tenant_isolation(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test retrieving installation token and preventing cross-tenant access."""
    # Org 1
    _, org1, token1 = await _create_test_user_and_org(
        db_session, "eng1@atip.dev", "Eng 1", "org-one", MembershipRole.DEVELOPER
    )
    # Register installation for Org 1
    service = get_github_app_service()
    await service.upsert_installation(
        db_session,
        organization_id=org1.id,
        installation_id=11223344,
        account_login="org-one-github",
        account_id=1122,
    )

    # Org 2
    _, org2, token2 = await _create_test_user_and_org(
        db_session, "eng2@atip.dev", "Eng 2", "org-two", MembershipRole.DEVELOPER
    )

    # 1. Eng 1 in Org 1 successfully retrieves token
    res1 = await client.get(
        "/api/v1/github/installations/11223344/token",
        headers={"Authorization": f"Bearer {token1}", "X-Organization-ID": org1.id},
    )
    assert res1.status_code == 200
    assert res1.json()["data"]["token"].startswith("ghs_inst_11223344")

    # 2. Eng 2 in Org 2 attempts to retrieve Org 1's installation token -> 404 NOT_FOUND
    res2 = await client.get(
        "/api/v1/github/installations/11223344/token",
        headers={"Authorization": f"Bearer {token2}", "X-Organization-ID": org2.id},
    )
    assert res2.status_code == 404
    assert res2.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_token_auto_rotation_on_expiration(
    db_session: AsyncSession,
) -> None:
    """Test that get_valid_installation_token automatically refreshes expired tokens."""
    service = get_github_app_service()
    installation = await service.upsert_installation(
        db_session,
        organization_id="org_test_rotation",
        installation_id=55667788,
        account_login="rot-org",
        account_id=5566,
    )
    initial_encrypted = installation.encrypted_token

    # Artificially expire the token in database
    installation.token_expires_at = datetime.now(UTC) - timedelta(minutes=10)
    await db_session.commit()

    # Request valid token: service must detect expiration, mint new token, and update DB
    new_token = await service.get_valid_installation_token(db_session, installation)
    assert new_token.startswith("ghs_inst_55667788")
    assert installation.token_expires_at > datetime.now(UTC)
    assert installation.encrypted_token != initial_encrypted


@pytest.mark.asyncio
async def test_github_token_login_and_user_repos(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test connecting with a GitHub token, fetching public/private repos, and querying user-repos."""
    _, org, token = await _create_test_user_and_org(
        db_session, "dev@atip.dev", "Dev User", "token-org", MembershipRole.DEVELOPER
    )

    # 1. Connect with token (using review token)
    response = await client.post(
        "/api/v1/github/token-login",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
        json={"token": "demo_github_pat_valid_123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["login"] == "developer-reviewer"
    assert len(data["repositories"]) >= 3
    # Check that both private and public repos are present
    assert any(r["is_private"] for r in data["repositories"])
    assert any(not r["is_private"] for r in data["repositories"])

    # 2. List user repos via GET /api/v1/github/user-repos
    repos_response = await client.get(
        "/api/v1/github/user-repos",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert repos_response.status_code == 200
    repos_data = repos_response.json()["data"]
    assert len(repos_data) >= 3
    assert repos_data[0]["full_name"] == "developer-reviewer/enterprise-backend"

