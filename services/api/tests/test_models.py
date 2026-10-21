"""Tests for core database models and relationships."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.db.models import (
    ExecutionJob,
    JobStatus,
    JobType,
    MembershipRole,
    Organization,
    OrganizationMembership,
    OutboxEvent,
    OutboxStatus,
    Repository,
    User,
)


@pytest.mark.asyncio
async def test_organization_and_user_creation(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Systems", slug="acme-systems")
    user = User(email="dev@example.com", name="Jane Developer")
    db_session.add_all([org, user])
    await db_session.flush()

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.OWNER,
    )
    db_session.add(membership)
    await db_session.flush()

    stmt = select(Organization).where(Organization.id == org.id)
    res = await db_session.execute(stmt)
    saved_org = res.scalar_one()

    assert saved_org.name == "Acme Systems"
    assert saved_org.slug == "acme-systems"
    assert len(saved_org.memberships) == 1
    assert saved_org.memberships[0].role == MembershipRole.OWNER


@pytest.mark.asyncio
async def test_repository_and_execution_job(db_session: AsyncSession) -> None:
    org = Organization(name="Security Org", slug="security-org")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=987654321,
        name="secure-api",
        full_name="security-org/secure-api",
        default_branch="main",
        clone_url="https://github.com/security-org/secure-api.git",
    )
    db_session.add(repo)
    await db_session.flush()

    job = ExecutionJob(
        organization_id=org.id,
        repository_id=repo.id,
        job_type=JobType.WHITEBOX_ANALYSIS,
        status=JobStatus.QUEUED,
        progress_pct=0,
    )
    db_session.add(job)
    await db_session.flush()

    assert job.id.startswith("job_")
    assert job.status == JobStatus.QUEUED
    assert job.job_type == JobType.WHITEBOX_ANALYSIS


@pytest.mark.asyncio
async def test_outbox_event_creation(db_session: AsyncSession) -> None:
    event = OutboxEvent(
        aggregate_type="repository",
        aggregate_id="repo_123",
        event_type="repository.synced",
        payload={"commit_sha": "abc1234"},
        status=OutboxStatus.PENDING,
    )
    db_session.add(event)
    await db_session.flush()

    assert event.id.startswith("out_")
    assert event.status == OutboxStatus.PENDING
