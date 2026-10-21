"""GitHub module schemas for installations, tokens, and webhooks."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GitHubInstallUrlResponse(BaseModel):
    install_url: str
    organization_id: str


class GitHubInstallationCreate(BaseModel):
    installation_id: int = Field(..., example=12345678)
    account_login: str = Field(..., example="octocat-org")
    account_id: int = Field(..., example=583231)
    target_type: str = Field(default="Organization", example="Organization")
    repository_selection: str = Field(default="selected", example="selected")
    permissions: dict[str, Any] | None = Field(default=None)


class GitHubInstallationRead(BaseModel):
    id: str
    organization_id: str
    installation_id: int
    account_login: str
    account_id: int
    target_type: str
    repository_selection: str
    permissions: dict[str, Any] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GitHubInstallationTokenResponse(BaseModel):
    token: str = Field(..., description="Masked or scoped installation token")
    token_type: str = "Bearer"
    expires_at: str


class WebhookReceiptResponse(BaseModel):
    status: str = Field(default="accepted")
    event: str
    delivery_id: str


class GitHubTokenConnectRequest(BaseModel):
    token: str = Field(..., min_length=4, description="GitHub Personal Access Token (classic or fine-grained)")


class GitHubUserProfile(BaseModel):
    login: str
    name: str | None = None
    avatar_url: str | None = None
    html_url: str | None = None
    public_repos: int = 0
    total_private_repos: int = 0


class GitHubRepoItem(BaseModel):
    id: int
    name: str
    full_name: str
    owner_login: str
    default_branch: str = "main"
    is_private: bool = False
    clone_url: str
    html_url: str
    language: str | None = None
    description: str | None = None
    updated_at: str | None = None
    is_connected: bool = False


class GitHubTokenConnectResponse(BaseModel):
    user: GitHubUserProfile
    repositories: list[GitHubRepoItem]
    installation_id: str

