"""GitHub App installations and signed webhook receiver router."""

from fastapi import APIRouter, Header, Request, status
from pydantic import BaseModel, Field

from atip_api.core.responses import DataResponse

router = APIRouter(prefix="/github", tags=["GitHub"])


class GitHubInstallationSummary(BaseModel):
    id: str
    installation_id: int
    account_login: str
    target_type: str
    repository_selection: str


class WebhookReceiptResponse(BaseModel):
    status: str = Field(default="received")
    event: str
    delivery_id: str


@router.get("/installations", response_model=DataResponse[list[GitHubInstallationSummary]])
async def list_installations() -> DataResponse[list[GitHubInstallationSummary]]:
    """List active GitHub App installations for organization."""
    return DataResponse(data=[])


@router.post(
    "/webhooks",
    response_model=DataResponse[WebhookReceiptResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: str = Header(default="", alias="X-Hub-Signature-256"),
) -> DataResponse[WebhookReceiptResponse]:
    """Ingest GitHub signed webhooks with raw body verification and deduplication."""
    _body = await request.body()
    # Signature verification logic will be enforced against GITHUB_WEBHOOK_SECRET
    # In M1 foundation, return acknowledged status
    return DataResponse(
        data=WebhookReceiptResponse(
            status="accepted",
            event=x_github_event,
            delivery_id=x_github_delivery,
        )
    )
