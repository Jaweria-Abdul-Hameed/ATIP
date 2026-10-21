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
