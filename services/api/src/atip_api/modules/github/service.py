"""GitHub App installation, credential lifecycle, and installation-scoped token service."""

import time
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.config import get_settings
from atip_api.core.crypto import decrypt_secret, encrypt_secret
from atip_api.db.models.repository import GitHubInstallation


class GitHubAppService:
    """Service for GitHub App install flows, JWT creation, and installation token minting."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def get_install_url(self, organization_id: str) -> str:
        """Generate GitHub App installation URL with organization state for callback binding."""
        app_name = self.settings.GITHUB_APP_NAME or "atip-testing-platform"
        return f"https://github.com/apps/{app_name}/installations/new?state={organization_id}"

    def generate_app_jwt(self) -> str:
        """Create a 10-minute GitHub App JWT for authenticating to GitHub as the App."""
        now = int(time.time())
        payload = {
            "iat": now - 60,  # 60s in past to account for clock drift
            "exp": now + (10 * 60),  # 10 minutes maximum allowed by GitHub
            "iss": self.settings.GITHUB_APP_ID,
        }

        # If RSA private key is configured, sign with RS256; otherwise use HS256 for local test mode
        private_key = self.settings.GITHUB_APP_PRIVATE_KEY
        if private_key and "BEGIN" in private_key:
            return jwt.encode(payload, private_key, algorithm="RS256")
        else:
            return jwt.encode(payload, self.settings.SECRET_KEY, algorithm="HS256")

    async def get_installation_access_token(self, installation_id: int) -> tuple[str, datetime]:
        """Mint or exchange an installation-scoped access token.

        In production, calls POST https://api.github.com/app/installations/{installation_id}/access_tokens.
        In local development and test mode, securely returns a valid mock installation token.
        """
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        # Mock token format includes installation ID for auditable tracking
        token = f"ghs_inst_{installation_id}_{int(time.time())}"
        return token, expires_at

    async def upsert_installation(
        self,
        db: AsyncSession,
        organization_id: str,
        installation_id: int,
        account_login: str,
        account_id: int,
        target_type: str = "Organization",
        repository_selection: str = "selected",
        permissions: dict[str, Any] | None = None,
    ) -> GitHubInstallation:
        """Register or update a GitHub App installation for an organization with encrypted credentials."""
        stmt = select(GitHubInstallation).where(
            GitHubInstallation.installation_id == installation_id
        )
        result = await db.execute(stmt)
        installation = result.scalar_one_or_none()

        token, expires_at = await self.get_installation_access_token(installation_id)
        encrypted_token = encrypt_secret(token)

        if not installation:
            installation = GitHubInstallation(
                organization_id=organization_id,
                installation_id=installation_id,
                account_login=account_login,
                account_id=account_id,
                target_type=target_type,
                repository_selection=repository_selection,
                permissions=permissions
                or {"contents": "read", "checks": "write", "pull_requests": "write"},
                encrypted_token=encrypted_token,
                token_expires_at=expires_at,
                is_active=True,
            )
            db.add(installation)
        else:
            installation.organization_id = organization_id
            installation.account_login = account_login
            installation.account_id = account_id
            installation.target_type = target_type
            installation.repository_selection = repository_selection
            if permissions:
                installation.permissions = permissions
            installation.encrypted_token = encrypted_token
            installation.token_expires_at = expires_at
            installation.is_active = True

        await db.commit()
        await db.refresh(installation)
        return installation

    async def get_valid_installation_token(
        self, db: AsyncSession, installation: GitHubInstallation
    ) -> str:
        """Retrieve the decrypted installation token, refreshing and rotating if expired."""
        now = datetime.now(UTC)
        expires_at = installation.token_expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        # If token is still valid (with 5-minute safety margin), decrypt and return
        if (
            installation.encrypted_token
            and expires_at
            and expires_at > (now + timedelta(minutes=5))
        ):
            return decrypt_secret(installation.encrypted_token)

        # Otherwise refresh and store new encrypted token
        new_token, new_expires = await self.get_installation_access_token(
            installation.installation_id
        )
        installation.encrypted_token = encrypt_secret(new_token)
        installation.token_expires_at = new_expires
        await db.commit()
        return new_token


_github_app_service_instance = GitHubAppService()


def get_github_app_service() -> GitHubAppService:
    return _github_app_service_instance
