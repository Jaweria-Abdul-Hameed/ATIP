"""Session management, JWT token generation, verification, and cookie utilities."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Response

from atip_api.config import get_settings
from atip_api.core.errors import SessionExpiredError, UnauthenticatedError

# In-memory revocation set for local/testing (complemented by Redis in clustered env)
_REVOKED_TOKENS: set[str] = set()


def create_session_token(
    user_id: str,
    email: str,
    name: str,
    org_ids: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """Create a signed JWT session token and return (token, expires_at)."""
    settings = get_settings()
    now = datetime.now(UTC)
    if expires_delta is not None:
        expires_at = now + expires_delta
    else:
        expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    session_id = f"ses_{uuid.uuid4().hex[:16]}"
    payload: dict[str, Any] = {
        "sub": user_id,
        "sid": session_id,
        "email": email,
        "name": name,
        "org_ids": org_ids or [],
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": settings.OIDC_ISSUER,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token, expires_at


def verify_session_token(token: str) -> dict[str, Any]:
    """Verify and decode a JWT session token.

    Raises:
        SessionExpiredError: If token expiration timestamp is in the past.
        UnauthenticatedError: If token is malformed, revoked, or signature invalid.
    """
    settings = get_settings()
    if token in _REVOKED_TOKENS:
        raise UnauthenticatedError(message="Session has been revoked. Please sign in again.")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            issuer=settings.OIDC_ISSUER,
            options={"require": ["sub", "exp", "iat"]},
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise SessionExpiredError(
            message="Session token has expired. Please sign in again."
        ) from e
    except jwt.PyJWTError as e:
        raise UnauthenticatedError(message=f"Invalid session token: {e}") from e


def revoke_session_token(token: str) -> None:
    """Add a session token to the revocation list."""
    _REVOKED_TOKENS.add(token)


def set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    """Set secure HTTP-only session cookie on the response."""
    settings = get_settings()
    max_age = int((expires_at - datetime.now(UTC)).total_seconds())
    if max_age < 0:
        max_age = 0

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        expires=expires_at,
        path="/",
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )


def clear_session_cookie(response: Response) -> None:
    """Clear session cookie on logout."""
    settings = get_settings()
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
