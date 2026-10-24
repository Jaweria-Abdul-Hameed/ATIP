"""Repository schemas matching frontend contract."""

from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryRead(BaseModel):
    id: str = Field(..., example="repo_nextjs_dashboard")
    organization_id: str | None = Field(default=None, example="org_default")
    name: str = Field(..., example="nextjs-dashboard")
    full_name: str = Field(..., example="acme/nextjs-dashboard")
    default_branch: str = Field(default="main", example="main")
    is_private: bool = Field(default=False)
    clone_url: str = Field(..., example="https://github.com/acme/nextjs-dashboard.git")
    language: str | None = Field(default="TypeScript", example="TypeScript")
    last_synced_at: str | None = Field(default=None, example="2026-10-21T09:30:00Z")
    created_at: datetime


class RepositoryDiscoverItem(BaseModel):
    github_repo_id: int = Field(..., example=123456)
    name: str = Field(..., example="api-service")
    full_name: str = Field(..., example="acme/api-service")
    default_branch: str = Field(default="main", example="main")
    is_private: bool = Field(default=False)
    clone_url: str = Field(..., example="https://github.com/acme/api-service.git")
    language: str | None = Field(default="Python", example="Python")
    is_connected: bool = Field(default=False)


class RepositoryConnectRequest(BaseModel):
    github_repo_id: int = Field(..., example=123456)
    name: str = Field(..., min_length=1, example="api-service")
    full_name: str = Field(..., min_length=1, example="acme/api-service")
    default_branch: str = Field(default="main", example="main")
    is_private: bool = Field(default=False)
    clone_url: str = Field(..., example="https://github.com/acme/api-service.git")
    language: str | None = Field(default=None, example="Python")
    github_installation_id: str | None = Field(default=None, example="ghi_123456")


class RepositoryConnectPublicUrlRequest(BaseModel):
    url: str = Field(..., min_length=3, example="https://github.com/pallets/flask")
    branch: str | None = Field(default=None, example="main")



class RepositorySyncResponse(BaseModel):
    repository_id: str
    status: str = Field(default="queued")
    job_id: str
    message: str = Field(default="Repository sync dispatched")


class BranchSummary(BaseModel):
    name: str = Field(..., example="main")
    commit_sha: str = Field(..., example="7960a5e8")
    is_default: bool = Field(default=False)


class PullRequestSummary(BaseModel):
    number: int = Field(..., example=42)
    title: str = Field(..., example="feat: add white-box test plan generation")
    state: str = Field(default="open", example="open")
    head_branch: str = Field(..., example="feat/white-box")
    head_sha: str = Field(..., example="7960a5e8")
    base_branch: str = Field(default="main", example="main")
    author: str = Field(..., example="octocat")
    created_at: str = Field(..., example="2026-10-21T08:00:00Z")
    updated_at: str = Field(..., example="2026-10-21T09:00:00Z")
