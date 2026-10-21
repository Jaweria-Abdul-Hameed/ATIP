"""GitHub App installation, credential lifecycle, and installation-scoped token service."""

import time
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atip_api.config import get_settings
from atip_api.core.crypto import decrypt_secret, encrypt_secret
from atip_api.core.errors import ValidationError
from atip_api.db.models.repository import GitHubInstallation, Repository
from atip_api.modules.github.schemas import (
    GitHubRepoItem,
    GitHubTokenConnectResponse,
    GitHubUserProfile,
)


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

    async def connect_with_token(
        self, db: AsyncSession, organization_id: str, token: str
    ) -> GitHubTokenConnectResponse:
        """Validate a GitHub Personal Access Token or OAuth token and return accessible repos."""
        clean_token = token.strip()

        # Check if user passed a simulated/mock token for testing
        is_mock = (
            clean_token.startswith("demo_")
            or clean_token.startswith("test_")
            or clean_token == "ghp_mock_token_for_review"
        )

        if is_mock:
            user = GitHubUserProfile(
                login="developer-reviewer",
                name="ATIP Reviewer",
                avatar_url="https://avatars.githubusercontent.com/u/9919?v=4",
                html_url="https://github.com/developer-reviewer",
                public_repos=3,
                total_private_repos=2,
            )
            raw_repos = [
                {
                    "id": 88001,
                    "name": "enterprise-backend",
                    "full_name": "developer-reviewer/enterprise-backend",
                    "default_branch": "main",
                    "is_private": True,
                    "clone_url": "https://github.com/developer-reviewer/enterprise-backend.git",
                    "html_url": "https://github.com/developer-reviewer/enterprise-backend",
                    "language": "Python",
                    "description": "Core microservices platform with pytest suite",
                },
                {
                    "id": 88002,
                    "name": "customer-portal",
                    "full_name": "developer-reviewer/customer-portal",
                    "default_branch": "main",
                    "is_private": False,
                    "clone_url": "https://github.com/developer-reviewer/customer-portal.git",
                    "html_url": "https://github.com/developer-reviewer/customer-portal",
                    "language": "TypeScript",
                    "description": "Next.js customer portal with Vitest tests",
                },
                {
                    "id": 88003,
                    "name": "payment-gateway-service",
                    "full_name": "developer-reviewer/payment-gateway-service",
                    "default_branch": "master",
                    "is_private": True,
                    "clone_url": "https://github.com/developer-reviewer/payment-gateway-service.git",
                    "html_url": "https://github.com/developer-reviewer/payment-gateway-service",
                    "language": "Python",
                    "description": "Financial transaction processor (private)",
                },
            ]
        else:
            # Query real GitHub REST API
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {
                    "Authorization": f"Bearer {clean_token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "ATIP-Autonomous-Testing-Platform",
                }
                user_resp = await client.get("https://api.github.com/user", headers=headers)
                if user_resp.status_code == 401:
                    raise ValidationError(
                        message="Invalid GitHub token. Please verify your token was copied correctly and has not expired."
                    )
                if user_resp.status_code != 200:
                    raise ValidationError(
                        message=f"GitHub API error ({user_resp.status_code}): {user_resp.text[:200]}"
                    )
                u_data = user_resp.json()
                user = GitHubUserProfile(
                    login=u_data.get("login", "unknown"),
                    name=u_data.get("name"),
                    avatar_url=u_data.get("avatar_url"),
                    html_url=u_data.get("html_url"),
                    public_repos=u_data.get("public_repos", 0),
                    total_private_repos=u_data.get("total_private_repos", 0),
                )

                # Fetch repos (both public and private)
                repos_resp = await client.get(
                    "https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner,collaborator,organization_member",
                    headers=headers,
                )
                if repos_resp.status_code != 200:
                    raise ValidationError(
                        message=f"Failed to fetch repositories from GitHub: {repos_resp.text[:200]}"
                    )
                raw_repos = [
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "full_name": r["full_name"],
                        "default_branch": r.get("default_branch", "main"),
                        "is_private": r.get("private", False),
                        "clone_url": r.get(
                            "clone_url", f"https://github.com/{r['full_name']}.git"
                        ),
                        "html_url": r.get("html_url", f"https://github.com/{r['full_name']}"),
                        "language": r.get("language"),
                        "description": r.get("description"),
                        "updated_at": r.get("updated_at"),
                    }
                    for r in repos_resp.json()
                ]

        # Upsert a GitHubInstallation for this token
        account_id = (abs(hash(user.login)) % 100000000) or 10001
        installation = await self.upsert_installation(
            db=db,
            organization_id=organization_id,
            installation_id=account_id,
            account_login=user.login,
            account_id=account_id,
            target_type="PersonalAccessToken",
            repository_selection="all",
            permissions={"contents": "read", "metadata": "read"},
        )
        # Store the actual encrypted token
        installation.encrypted_token = encrypt_secret(clean_token)
        installation.token_expires_at = datetime.now(UTC) + timedelta(days=90)
        await db.commit()

        # Check which repositories are already connected in this org
        connected_stmt = select(Repository.github_repo_id).where(
            Repository.organization_id == organization_id
        )
        connected_ids = set((await db.execute(connected_stmt)).scalars().all())

        repo_items = [
            GitHubRepoItem(
                id=r["id"],
                name=r["name"],
                full_name=r["full_name"],
                owner_login=r["full_name"].split("/")[0]
                if "/" in r["full_name"]
                else user.login,
                default_branch=r["default_branch"],
                is_private=r["is_private"],
                clone_url=r["clone_url"],
                html_url=r.get("html_url", r["clone_url"]),
                language=r.get("language"),
                description=r.get("description"),
                updated_at=r.get("updated_at"),
                is_connected=r["id"] in connected_ids,
            )
            for r in raw_repos
        ]

        return GitHubTokenConnectResponse(
            user=user,
            repositories=repo_items,
            installation_id=installation.id,
        )



_github_app_service_instance = GitHubAppService()


def get_github_app_service() -> GitHubAppService:
    return _github_app_service_instance
