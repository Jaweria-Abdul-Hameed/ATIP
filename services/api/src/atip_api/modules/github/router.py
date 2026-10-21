"""GitHub App installations and signed webhook receiver router."""

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.core.errors import NotFoundError
from atip_api.core.responses import DataResponse
from atip_api.db.models.organization import MembershipRole, User
from atip_api.db.models.repository import GitHubInstallation
from atip_api.db.session import get_db
from atip_api.modules.github.schemas import (
    GitHubInstallationCreate,
    GitHubInstallationRead,
    GitHubInstallationTokenResponse,
    GitHubInstallUrlResponse,
    WebhookReceiptResponse,
)
from atip_api.modules.github.service import get_github_app_service
from atip_api.modules.github.webhook import get_webhook_service
from atip_api.modules.identity.deps import get_optional_current_user
from atip_api.modules.organizations.deps import OrgContext, get_org_context, require_org_role

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.get("/install-url", response_model=DataResponse[GitHubInstallUrlResponse])
async def get_install_url(
    context: OrgContext = Depends(require_org_role(MembershipRole.ADMIN)),
) -> DataResponse[GitHubInstallUrlResponse]:
    """Generate GitHub App installation redirect URL for current organization."""
    service = get_github_app_service()
    url = service.get_install_url(context.organization.id)
    return DataResponse(
        data=GitHubInstallUrlResponse(
            install_url=url,
            organization_id=context.organization.id,
        )
    )


@router.get("/callback", response_model=DataResponse[GitHubInstallationRead])
async def github_app_callback(
    installation_id: int = Query(...),
    setup_action: str = Query(default="install"),
    state: str | None = Query(default=None),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[GitHubInstallationRead]:
    """Callback route invoked by GitHub after App installation."""
    service = get_github_app_service()

    # Determine organization: from state or user's first org
    target_org_id = state
    if not target_org_id and current_user and current_user.memberships:
        target_org_id = current_user.memberships[0].organization_id
    elif not target_org_id:
        target_org_id = "org_default_workspace"

    installation = await service.upsert_installation(
        db=db,
        organization_id=target_org_id,
        installation_id=installation_id,
        account_login=f"github-org-{installation_id}",
        account_id=installation_id,
    )

    return DataResponse(
        data=GitHubInstallationRead(
            id=installation.id,
            organization_id=installation.organization_id,
            installation_id=installation.installation_id,
            account_login=installation.account_login,
            account_id=installation.account_id,
            target_type=installation.target_type,
            repository_selection=installation.repository_selection,
            permissions=installation.permissions,
            is_active=installation.is_active,
            created_at=installation.created_at,
            updated_at=installation.updated_at,
        )
    )


@router.post(
    "/installations",
    response_model=DataResponse[GitHubInstallationRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_installation(
    payload: GitHubInstallationCreate,
    context: OrgContext = Depends(require_org_role(MembershipRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[GitHubInstallationRead]:
    """Register or link a GitHub App installation to the organization."""
    service = get_github_app_service()
    installation = await service.upsert_installation(
        db=db,
        organization_id=context.organization.id,
        installation_id=payload.installation_id,
        account_login=payload.account_login,
        account_id=payload.account_id,
        target_type=payload.target_type,
        repository_selection=payload.repository_selection,
        permissions=payload.permissions,
    )

    return DataResponse(
        data=GitHubInstallationRead(
            id=installation.id,
            organization_id=installation.organization_id,
            installation_id=installation.installation_id,
            account_login=installation.account_login,
            account_id=installation.account_id,
            target_type=installation.target_type,
            repository_selection=installation.repository_selection,
            permissions=installation.permissions,
            is_active=installation.is_active,
            created_at=installation.created_at,
            updated_at=installation.updated_at,
        )
    )


@router.get("/installations", response_model=DataResponse[list[GitHubInstallationRead]])
async def list_installations(
    context: OrgContext = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[list[GitHubInstallationRead]]:
    """List active GitHub App installations for organization."""
    stmt = select(GitHubInstallation).where(
        GitHubInstallation.organization_id == context.organization.id,
        GitHubInstallation.is_active.is_(True),
    )
    result = await db.execute(stmt)
    installations = result.scalars().all()

    items = [
        GitHubInstallationRead(
            id=inst.id,
            organization_id=inst.organization_id,
            installation_id=inst.installation_id,
            account_login=inst.account_login,
            account_id=inst.account_id,
            target_type=inst.target_type,
            repository_selection=inst.repository_selection,
            permissions=inst.permissions,
            is_active=inst.is_active,
            created_at=inst.created_at,
            updated_at=inst.updated_at,
        )
        for inst in installations
    ]
    return DataResponse(data=items)


@router.get(
    "/installations/{installation_id}/token",
    response_model=DataResponse[GitHubInstallationTokenResponse],
)
async def get_installation_token(
    installation_id: int,
    context: OrgContext = Depends(require_org_role(MembershipRole.DEVELOPER)),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[GitHubInstallationTokenResponse]:
    """Retrieve an active installation token for authorized repository operations."""
    stmt = select(GitHubInstallation).where(
        GitHubInstallation.organization_id == context.organization.id,
        GitHubInstallation.installation_id == installation_id,
        GitHubInstallation.is_active.is_(True),
    )
    result = await db.execute(stmt)
    installation = result.scalar_one_or_none()

    if not installation:
        raise NotFoundError(
            message=f"GitHub installation '{installation_id}' not found in organization."
        )

    service = get_github_app_service()
    token = await service.get_valid_installation_token(db, installation)

    return DataResponse(
        data=GitHubInstallationTokenResponse(
            token=token,
            token_type="Bearer",
            expires_at=installation.token_expires_at.isoformat()
            if installation.token_expires_at
            else "",
        )
    )


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
    db: AsyncSession = Depends(get_db),
) -> DataResponse[WebhookReceiptResponse]:
    """Ingest GitHub signed webhooks with raw body verification, deduplication, and transactional outbox persistence."""
    raw_body = await request.body()
    service = get_webhook_service()
    receipt = await service.ingest_webhook(
        raw_body=raw_body,
        event=x_github_event,
        delivery_id=x_github_delivery,
        signature=x_hub_signature_256,
        db=db,
    )
    return DataResponse(data=receipt)
