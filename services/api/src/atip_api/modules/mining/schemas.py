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


class CommitRead(BaseModel):
    id: str
    repository_id: str
    organization_id: str
    commit_sha: str
    tree_sha: str | None = None
    parent_shas: list[str] | None = None
    author_name: str | None = None
    author_email: str | None = None
    committer_name: str | None = None
    committer_email: str | None = None
    committed_at: str | None = None
    summary: str | None = None
    message: str = ""
    insertions: int = 0
    deletions: int = 0
    files_changed_count: int = 0
    created_at: str

    model_config = {"from_attributes": True}


class FileChangeRead(BaseModel):
    id: str
    commit_sha: str
    file_path: str
    previous_path: str | None = None
    change_type: str
    insertions: int = 0
    deletions: int = 0
    is_test: bool = False
    language: str | None = None
    patch: str | None = None

    model_config = {"from_attributes": True}


class CommitDetailRead(BaseModel):
    commit: CommitRead
    file_changes: list[FileChangeRead]


class HotspotRead(BaseModel):
    file_path: str
    change_count: int
    total_insertions: int
    total_deletions: int
    total_churn: int
    distinct_authors_count: int
    primary_owner: str
    ownership_pct: float
    authors: dict[str, int]
    is_test: bool
    language: str | None = None
    hotspot_score: float
    last_modified: str | None = None


class MineHistoryRequest(BaseModel):
    branch: str = Field(default="HEAD", description="Branch name or ref to mine")
    max_commits: int = Field(default=50, ge=1, le=500, description="Max commits to extract")


class DependencyEdgeRead(BaseModel):
    source: str
    target: str
    target_module: str
    target_file: str | None = None
    is_external: bool = False
    import_type: str
    line: int = 1


class DependencyNodeRead(BaseModel):
    id: str
    file_path: str
    fan_in: int = 0
    fan_out: int = 0
    dependencies: list[str] = Field(default_factory=list)
    dependents: list[str] = Field(default_factory=list)


class DependencyGraphRead(BaseModel):
    commit_sha: str
    total_nodes: int
    total_edges: int
    internal_edges_count: int
    external_edges_count: int
    circular_cycles: list[list[str]] = Field(default_factory=list)
    nodes: list[DependencyNodeRead]
    edges: list[DependencyEdgeRead]


class FileDependencyDetailRead(BaseModel):
    file_path: str
    direct_dependencies: list[DependencyEdgeRead]
    reverse_dependents: list[DependencyEdgeRead]
    blast_radius_count: int
