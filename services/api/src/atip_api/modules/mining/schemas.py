"""Pydantic schemas for repository mining and snapshot APIs."""

from typing import Any

from pydantic import BaseModel, Field


class SnapshotCreateRequest(BaseModel):
    ref: str = Field(default="HEAD", description="Branch name, tag, or commit reference")
    commit_sha: str | None = Field(default=None, description="Explicit 40-char commit SHA if known")


class SnapshotRead(BaseModel):
    id: str
    repository_id: str
    organization_id: str
    commit_sha: str
    tree_sha: str | None = None
    parent_shas: list[str] | None = None
    branch_name: str
    ref: str
    summary: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    committed_at: str | None = None
    stats_json: dict[str, Any] | None = None
    created_at: str

    model_config = {"from_attributes": True}


class SnapshotTreeItem(BaseModel):
    path: str
    type: str = "blob"
    size_bytes: int = 0
    sha: str = ""


class SnapshotFileContent(BaseModel):
    path: str
    commit_sha: str
    size_bytes: int
    content: str
    is_binary: bool = False
