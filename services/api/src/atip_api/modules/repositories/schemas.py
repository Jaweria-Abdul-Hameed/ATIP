"""Repository schemas matching frontend contract."""

from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryRead(BaseModel):
    id: str = Field(..., example="repo_nextjs_dashboard")
    name: str = Field(..., example="nextjs-dashboard")
    full_name: str = Field(..., example="acme/nextjs-dashboard")
    default_branch: str = Field(default="main", example="main")
    is_private: bool = Field(default=False)
    clone_url: str = Field(..., example="https://github.com/acme/nextjs-dashboard.git")
    language: str | None = Field(default="TypeScript", example="TypeScript")
    last_synced_at: str | None = Field(default=None, example="2026-10-21T09:30:00Z")
    created_at: datetime


class RepositorySyncResponse(BaseModel):
    repository_id: str
    status: str = Field(default="queued")
    job_id: str
    message: str = Field(default="Repository sync dispatched")


class BranchSummary(BaseModel):
    name: str = Field(..., example="main")
    commit_sha: str = Field(..., example="7960a5e8")
    is_default: bool = Field(default=False)
