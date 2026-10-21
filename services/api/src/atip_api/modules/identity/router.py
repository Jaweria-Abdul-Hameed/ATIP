"""Identity and Authentication router implementing OIDC, sessions, and user profile."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from atip_api.core.responses import DataResponse
from atip_api.db.models.organization import (
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from atip_api.db.session import get_db
from atip_api.modules.identity.deps import (
    extract_token_from_request,
    get_current_active_user,
    get_optional_current_user,
)
from atip_api.modules.identity.oidc import get_oidc_client
from atip_api.modules.identity.schemas import (
    AuthCallbackRequest,
    AuthLoginResponse,
    AuthSessionResponse,
    LogoutResponse,
    OrganizationSummary,
    UserProfile,
)
from atip_api.modules.identity.session import (
    clear_session_cookie,
    create_session_token,
    revoke_session_token,
    set_session_cookie,
)

router = APIRouter()


def _build_user_profile(user: User) -> UserProfile:
    """Helper to convert User DB entity to UserProfile schema."""
    org_summaries = []
    for m in user.memberships:
        if m.organization and m.organization.is_active:
            org_summaries.append(
                OrganizationSummary(
                    id=m.organization.id,
                    slug=m.organization.slug,
                    name=m.organization.name,
                    role=m.role.value if hasattr(m.role, "value") else str(m.role),
                )
            )

    return UserProfile(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        organizations=org_summaries,
    )


# ---------------------------------------------------------------------------
# Authentication endpoints: /api/v1/auth/*
# ---------------------------------------------------------------------------


@router.get("/auth/login", response_model=DataResponse[AuthLoginResponse], tags=["Authentication"])
async def auth_login(
    redirect_uri: str | None = Query(default=None),
) -> DataResponse[AuthLoginResponse]:
    """Generate OIDC authorization URL and state token."""
    oidc = get_oidc_client()
    auth_url, state, _ = oidc.generate_authorization_url(redirect_uri=redirect_uri)
    return DataResponse(
        data=AuthLoginResponse(
            authorization_url=auth_url,
            state=state,
        )
    )


@router.post(
    "/auth/callback",
    response_model=DataResponse[AuthSessionResponse],
    tags=["Authentication"],
)
async def auth_callback_post(
    payload: AuthCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> DataResponse[AuthSessionResponse]:
    """Process OIDC code exchange, upsert user and org, and establish secure session."""
    return await _handle_auth_callback(
        code=payload.code,
        state=payload.state,
        redirect_uri=payload.redirect_uri,
        response=response,
        db=db,
    )


@router.get(
    "/auth/callback",
    response_model=DataResponse[AuthSessionResponse],
    tags=["Authentication"],
)
async def auth_callback_get(
    response: Response,
    code: str = Query(..., min_length=1),
    state: str = Query(..., min_length=1),
    redirect_uri: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> DataResponse[AuthSessionResponse]:
    """GET callback handler for standard browser OIDC redirects."""
    return await _handle_auth_callback(
        code=code,
        state=state,
        redirect_uri=redirect_uri,
        response=response,
        db=db,
    )


async def _handle_auth_callback(
    code: str,
    state: str,
    redirect_uri: str | None,
    response: Response,
    db: AsyncSession,
) -> DataResponse[AuthSessionResponse]:
    oidc = get_oidc_client()
    oidc_user = await oidc.exchange_code_for_user(code=code, state=state, redirect_uri=redirect_uri)

    # Find or create user
    stmt = (
        select(User)
        .options(selectinload(User.memberships).selectinload(OrganizationMembership.organization))
        .where(User.email == oidc_user.email)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=oidc_user.email,
            name=oidc_user.name,
            avatar_url=oidc_user.avatar_url,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        # Create default organization workspace for new user
        slug_base = oidc_user.email.split("@")[0].lower()
        clean_slug = "".join(c for c in slug_base if c.isalnum() or c == "-") or "workspace"
        unique_slug = f"{clean_slug}-{user.id[:8]}"
        org = Organization(
            name=f"{oidc_user.name}'s Workspace",
            slug=unique_slug,
            billing_tier="team",
            is_active=True,
        )
        db.add(org)
        await db.flush()

        # Assign user as Owner
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role=MembershipRole.OWNER,
        )
        db.add(membership)
        await db.commit()

        # Re-fetch with relationships loaded
        result = await db.execute(stmt)
        user = result.scalar_one()
    else:
        # Update name and avatar if changed
        if user.name != oidc_user.name or user.avatar_url != oidc_user.avatar_url:
            user.name = oidc_user.name
            user.avatar_url = oidc_user.avatar_url
            await db.commit()

    # Generate session token and set secure HTTP-only cookie
    org_ids = [m.organization_id for m in user.memberships]
    token, expires_at = create_session_token(
        user_id=user.id,
        email=user.email,
        name=user.name,
        org_ids=org_ids,
    )
    set_session_cookie(response, token, expires_at)

    profile = _build_user_profile(user)
    return DataResponse(
        data=AuthSessionResponse(
            authenticated=True,
            user=profile,
            token=token,
            expires_at=expires_at.isoformat(),
        )
    )


@router.post(
    "/auth/logout",
    response_model=DataResponse[LogoutResponse],
    tags=["Authentication"],
)
async def auth_logout(
    request: Request,
    response: Response,
) -> DataResponse[LogoutResponse]:
    """Logout current user: invalidate session token and clear HTTP-only cookie."""
    token = extract_token_from_request(request)
    if token:
        revoke_session_token(token)

    clear_session_cookie(response)
    return DataResponse(data=LogoutResponse())


@router.get(
    "/auth/session",
    response_model=DataResponse[AuthSessionResponse],
    tags=["Authentication"],
)
async def auth_session(
    user: User | None = Depends(get_optional_current_user),
) -> DataResponse[AuthSessionResponse]:
    """Inspect active session status."""
    if not user:
        return DataResponse(
            data=AuthSessionResponse(
                authenticated=False,
                user=None,
                token=None,
                expires_at=None,
            )
        )

    profile = _build_user_profile(user)
    return DataResponse(
        data=AuthSessionResponse(
            authenticated=True,
            user=profile,
        )
    )


# ---------------------------------------------------------------------------
# Identity endpoint: /api/v1/me (Protected route)
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=DataResponse[UserProfile],
    tags=["Identity"],
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> DataResponse[UserProfile]:
    """Retrieve profile and organizations for the authenticated user."""
    profile = _build_user_profile(current_user)
    return DataResponse(data=profile)
