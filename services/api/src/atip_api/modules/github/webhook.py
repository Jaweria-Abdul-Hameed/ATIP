"""Signed GitHub webhook verification, replay protection, delivery deduplication, and durable outbox ingestion."""

import hashlib
import hmac
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.config import get_settings
from atip_api.core.errors import APIException
from atip_api.db.models.outbox import OutboxEvent, OutboxStatus
from atip_api.modules.github.schemas import WebhookReceiptResponse

# In-memory deduplication cache for rapid replay defense (supplements DB outbox)
_PROCESSED_DELIVERIES: set[str] = set()


def verify_github_signature(
    raw_body: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    """Verify HMAC-SHA256 signature on the raw request payload against configured secret.

    Signature header format: 'sha256=<hex_digest>'
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header.removeprefix("sha256=")
    computed_hmac = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed_hmac, expected_signature)


class WebhookIngestionService:
    """Service handling signed webhook verification, deduplication, and transactional outbox persistence."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def ingest_webhook(
        self,
        raw_body: bytes,
        event: str,
        delivery_id: str,
        signature: str | None,
        db: AsyncSession,
    ) -> WebhookReceiptResponse:
        """Verify, deduplicate, and durably ingest a GitHub webhook into the transactional outbox."""
        # 1. Verify HMAC-SHA256 signature on raw bytes
        if not verify_github_signature(raw_body, signature, self.settings.GITHUB_WEBHOOK_SECRET):
            raise APIException(
                code="WEBHOOK_SIGNATURE_INVALID",
                message="GitHub webhook HMAC-SHA256 signature verification failed.",
                status_code=401,
            )

        # 2. Check deduplication in-memory and database
        if delivery_id in _PROCESSED_DELIVERIES:
            return WebhookReceiptResponse(
                status="duplicate",
                event=event,
                delivery_id=delivery_id,
            )

        existing_stmt = select(OutboxEvent).where(
            OutboxEvent.aggregate_type == "github_webhook",
            OutboxEvent.aggregate_id == delivery_id,
        )
        existing_event = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing_event:
            _PROCESSED_DELIVERIES.add(delivery_id)
            return WebhookReceiptResponse(
                status="duplicate",
                event=event,
                delivery_id=delivery_id,
            )

        # 3. Parse JSON body
        try:
            payload: dict[str, Any] = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            payload = {}

        # 4. Handle ping events immediately
        if event == "ping":
            _PROCESSED_DELIVERIES.add(delivery_id)
            return WebhookReceiptResponse(
                status="accepted",
                event="ping",
                delivery_id=delivery_id,
            )

        # 5. Persist into Transactional Outbox for durable asynchronous worker processing
        outbox_entry = OutboxEvent(
            aggregate_type="github_webhook",
            aggregate_id=delivery_id,
            event_type=f"github.{event}",
            payload={
                "event": event,
                "delivery_id": delivery_id,
                "action": payload.get("action"),
                "repository": payload.get("repository", {}).get("full_name")
                if isinstance(payload.get("repository"), dict)
                else None,
                "installation_id": payload.get("installation", {}).get("id")
                if isinstance(payload.get("installation"), dict)
                else None,
                "raw_payload": payload,
            },
            status=OutboxStatus.PENDING,
        )
        db.add(outbox_entry)
        await db.commit()

        _PROCESSED_DELIVERIES.add(delivery_id)

        return WebhookReceiptResponse(
            status="accepted",
            event=event,
            delivery_id=delivery_id,
        )


_webhook_ingestion_service = WebhookIngestionService()


def get_webhook_service() -> WebhookIngestionService:
    return _webhook_ingestion_service
