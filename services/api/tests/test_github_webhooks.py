"""Tests for signed GitHub webhook verification, replay protection, deduplication, and outbox persistence."""

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.config import get_settings
from atip_api.db.models.outbox import OutboxEvent, OutboxStatus


def _compute_github_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_webhook_rejects_missing_or_invalid_signature(client: AsyncClient) -> None:
    """Test webhook endpoint rejects requests with missing or forged HMAC signature."""
    payload = json.dumps({"zen": "Keep it logically awesome."}).encode("utf-8")

    # 1. Missing signature
    res1 = await client.post(
        "/api/v1/github/webhooks",
        content=payload,
        headers={
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "deliv_no_sig_123",
            "Content-Type": "application/json",
        },
    )
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "WEBHOOK_SIGNATURE_INVALID"

    # 2. Forged signature
    res2 = await client.post(
        "/api/v1/github/webhooks",
        content=payload,
        headers={
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "deliv_bad_sig_123",
            "X-Hub-Signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000",
            "Content-Type": "application/json",
        },
    )
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "WEBHOOK_SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_webhook_ingests_valid_push_event_into_outbox(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test validly signed push event is persisted into the transactional outbox."""
    settings = get_settings()
    payload_dict = {
        "ref": "refs/heads/main",
        "before": "0000000000000000000000000000000000000000",
        "after": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
        "repository": {
            "id": 1296269,
            "name": "Hello-World",
            "full_name": "octocat/Hello-World",
            "private": False,
        },
        "commits": [
            {
                "id": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                "message": "feat: add autonomous white-box test suite",
            }
        ],
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    signature = _compute_github_signature(raw_body, settings.GITHUB_WEBHOOK_SECRET)
    delivery_id = "deliv_push_valid_001"

    response = await client.post(
        "/api/v1/github/webhooks",
        content=raw_body,
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 202
    data = response.json()["data"]
    assert data["status"] == "accepted"
    assert data["event"] == "push"
    assert data["delivery_id"] == delivery_id

    # Verify event in PostgreSQL Transactional Outbox
    stmt = select(OutboxEvent).where(
        OutboxEvent.aggregate_type == "github_webhook",
        OutboxEvent.aggregate_id == delivery_id,
    )
    outbox_event = (await db_session.execute(stmt)).scalar_one()
    assert outbox_event.event_type == "github.push"
    assert outbox_event.status == OutboxStatus.PENDING
    assert outbox_event.payload["repository"] == "octocat/Hello-World"


@pytest.mark.asyncio
async def test_webhook_deduplication(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that redelivering the same webhook delivery ID is deduplicated idempotently."""
    settings = get_settings()
    raw_body = json.dumps({"action": "opened", "number": 42}).encode("utf-8")
    signature = _compute_github_signature(raw_body, settings.GITHUB_WEBHOOK_SECRET)
    delivery_id = "deliv_pr_dedup_002"

    # First delivery
    res1 = await client.post(
        "/api/v1/github/webhooks",
        content=raw_body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert res1.status_code == 202
    assert res1.json()["data"]["status"] == "accepted"

    # Redelivery (replay / duplicate webhook)
    res2 = await client.post(
        "/api/v1/github/webhooks",
        content=raw_body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert res2.status_code == 202
    assert res2.json()["data"]["status"] == "duplicate"

    # Verify only 1 outbox entry exists in database
    stmt = select(OutboxEvent).where(
        OutboxEvent.aggregate_type == "github_webhook",
        OutboxEvent.aggregate_id == delivery_id,
    )
    entries = (await db_session.execute(stmt)).scalars().all()
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_webhook_baseline_alias_route(client: AsyncClient) -> None:
    """Test /api/v1/webhooks/github alias endpoint works seamlessly."""
    settings = get_settings()
    raw_body = json.dumps({"zen": "Practicality beats purity."}).encode("utf-8")
    signature = _compute_github_signature(raw_body, settings.GITHUB_WEBHOOK_SECRET)
    delivery_id = "deliv_alias_route_003"

    response = await client.post(
        "/api/v1/webhooks/github",
        content=raw_body,
        headers={
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 202
    assert response.json()["data"]["event"] == "ping"
