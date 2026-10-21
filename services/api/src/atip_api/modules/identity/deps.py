"""FastAPI authentication dependencies for protected routes and user identity."""

from typing import Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from atip_api.config import get_settings
from atip_api.core.errors import ForbiddenError, UnauthenticatedError
from atip_api.db.models.organization import OrganizationMembership, User
from atip_api.db.session import get_db
from atip_api.modules.identity.session import verify_session_token


def extract_token_from_request(request: Request) -> str | None:
    """Extract session token from Authorization header or HTTP-only session cookie."""
    settings = get_settings()

    # 1. Check Authorization header: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        if token:
            return token

    # 2. Check HTTP-only session cookie
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


def get_current_session_payload(request: Request) -> dict[str, Any]:
    """Retrieve and verify the active session token payload.

    Raises UnauthenticatedError if missing or invalid, SessionExpiredError if expired.
    """
    token = extract_token_from_request(request)
    if not token:
        raise UnauthenticatedError(
            message="Authentication required: No active session or token found."
        )

    return verify_session_token(token)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Retrieve the authenticated User database entity with memberships loaded."""
    payload = get_current_session_payload(request)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthenticatedError(message="Malformed session token: missing subject.")

    query = (
        select(User)
        .options(
            selectinload(User.memberships).selectinload(OrganizationMembership.organization),
        )
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthenticatedError(
            message="User account associated with this session no longer exists."
        )

    if not user.is_active:
        raise ForbiddenError(message="User account has been deactivated.")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise ForbiddenError(message="Inactive user account.")
    return current_user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optional user dependency for routes that can render both public and authenticated states."""
    try:
        return await get_current_user(request, db)
    except Exception:
        return None
