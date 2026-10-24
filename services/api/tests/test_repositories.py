"""Tests for repository discovery, connecting, sync, branch/PR selectors, and tenant isolation."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models import (
    ExecutionJob,
    JobStatus,
    JobType,
    Organization,
    OrganizationMembership,
    Repository,
    User,
)
from atip_api.db.models.organization import MembershipRole
from atip_api.db.models.outbox import OutboxEvent
from atip_api.modules.identity.session import create_session_token


async def _create_test_env(
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


@pytest.mark.asyncio
async def test_repository_discovery_and_connect(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test discovering repositories and connecting a repo with initial mining job."""
    _, org, token = await _create_test_env(
        db_session, "dev@atip.dev", "Dev User", "acme-corp", MembershipRole.ADMIN
    )

    # 1. Discover repositories
    disc_res = await client.get(
        "/api/v1/repositories/discover?query=api",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert "data" in disc_data
    assert len(disc_data["data"]) > 0
    assert "core-api" in disc_data["data"][0]["name"]

    # 2. Connect repository
    target_repo = disc_data["data"][0]
    conn_res = await client.post(
        "/api/v1/repositories/connect",
        json={
            "github_repo_id": target_repo["github_repo_id"],
            "name": target_repo["name"],
            "full_name": target_repo["full_name"],
            "default_branch": target_repo["default_branch"],
            "is_private": target_repo["is_private"],
            "clone_url": target_repo["clone_url"],
            "language": target_repo["language"],
        },
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert conn_res.status_code == 201
    repo_data = conn_res.json()["data"]
    assert repo_data["name"] == target_repo["name"]
    repo_id = repo_data["id"]

    # Verify initial REPO_MINING execution job was queued
    stmt = select(ExecutionJob).where(
        ExecutionJob.repository_id == repo_id,
        ExecutionJob.job_type == JobType.REPO_MINING,
    )
    job = (await db_session.execute(stmt)).scalar_one()
    assert job.status == JobStatus.QUEUED


@pytest.mark.asyncio
async def test_repository_sync_and_outbox(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test repository sync endpoint queues job and creates outbox event."""
    _, org, token = await _create_test_env(
        db_session, "lead@atip.dev", "Lead", "sync-org", MembershipRole.DEVELOPER
    )

    # Create connected repository directly in DB
    repo = Repository(
        organization_id=org.id,
        github_repo_id=555001,
        name="backend-service",
        full_name="sync-org/backend-service",
        default_branch="main",
        is_private=True,
        clone_url="https://github.com/sync-org/backend-service.git",
        language="Python",
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    # Trigger sync
    sync_res = await client.post(
        f"/api/v1/repositories/{repo.id}/sync",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert sync_res.status_code == 200
    sync_data = sync_res.json()["data"]
    assert sync_data["status"] == "queued"
    job_id = sync_data["job_id"]

    # Verify job and outbox event
    job = (
        await db_session.execute(select(ExecutionJob).where(ExecutionJob.id == job_id))
    ).scalar_one()
    assert job.status == JobStatus.QUEUED

    outbox = (
        await db_session.execute(
            select(OutboxEvent).where(
                OutboxEvent.aggregate_id == repo.id,
                OutboxEvent.event_type == "repository.sync_requested",
            )
        )
    ).scalar_one()
    assert outbox.payload["job_id"] == job_id


@pytest.mark.asyncio
async def test_branch_and_pr_selectors(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test branch and PR selectors return expected lists with default branches and commit SHAs."""
    _, org, token = await _create_test_env(
        db_session, "qa@atip.dev", "QA Engineer", "qa-org", MembershipRole.DEVELOPER
    )

    repo = Repository(
        organization_id=org.id,
        github_repo_id=777002,
        name="web-app",
        full_name="qa-org/web-app",
        default_branch="main",
        is_private=False,
        clone_url="https://github.com/qa-org/web-app.git",
        language="TypeScript",
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    # Branches
    branches_res = await client.get(
        f"/api/v1/repositories/{repo.id}/branches",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert branches_res.status_code == 200
    branches = branches_res.json()["data"]
    assert len(branches) >= 2
    assert any(b["name"] == "main" and b["is_default"] for b in branches)

    # PRs
    prs_res = await client.get(
        f"/api/v1/repositories/{repo.id}/pull-requests",
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert prs_res.status_code == 200
    prs = prs_res.json()["data"]
    assert len(prs) >= 1
    assert prs[0]["head_branch"] is not None
    assert prs[0]["head_sha"] is not None


@pytest.mark.asyncio
async def test_repository_tenant_isolation(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test accessing a repository belonging to another tenant returns 404."""
    # Tenant 1
    _, org1, _ = await _create_test_env(
        db_session, "user1@atip.dev", "User 1", "tenant-one", MembershipRole.ADMIN
    )
    repo1 = Repository(
        organization_id=org1.id,
        github_repo_id=888001,
        name="secret-repo",
        full_name="tenant-one/secret-repo",
        default_branch="main",
        is_private=True,
        clone_url="https://github.com/tenant-one/secret-repo.git",
    )
    db_session.add(repo1)
    await db_session.commit()
    await db_session.refresh(repo1)

    # Tenant 2
    _, org2, token2 = await _create_test_env(
        db_session, "user2@atip.dev", "User 2", "tenant-two", MembershipRole.ADMIN
    )

    # User 2 in Tenant 2 attempts to view Tenant 1's repository
    res = await client.get(
        f"/api/v1/repositories/{repo1.id}",
        headers={"Authorization": f"Bearer {token2}", "X-Organization-ID": org2.id},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_connect_public_repository_by_url(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test connecting an arbitrary public repository by URL without GitHub credentials."""
    _, org, token = await _create_test_env(
        db_session, "public_dev@atip.dev", "Public Dev", "public-org", MembershipRole.DEVELOPER
    )

    # 1. Connect public repository by URL
    res = await client.post(
        "/api/v1/repositories/connect-public-url",
        json={"url": "https://github.com/pallets/flask", "branch": "main"},
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["name"] == "flask"
    assert data["full_name"] == "pallets/flask"
    assert data["clone_url"] == "https://github.com/pallets/flask.git"
    assert data["is_private"] is False
    assert data["default_branch"] == "main"

    # 2. Duplicate connection rejected
    dup_res = await client.post(
        "/api/v1/repositories/connect-public-url",
        json={"url": "https://github.com/pallets/flask"},
        headers={"Authorization": f"Bearer {token}", "X-Organization-ID": org.id},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "CONFLICT"
