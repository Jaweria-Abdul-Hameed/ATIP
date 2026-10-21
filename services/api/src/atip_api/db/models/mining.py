"""Mining and static analysis database models."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atip_api.db.base import Base, OrgScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from atip_api.db.models.job import ExecutionJob
    from atip_api.db.models.repository import Repository


class ChangeType(str, enum.Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CommitRecord(Base, TimestampMixin, OrgScopedMixin):
    """Immutable commit history record mined from repository."""

    __tablename__ = "commits"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"cmt_{uuid.uuid4().hex[:16]}",
    )
    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tree_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_shas: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    committer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    committer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    insertions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deletions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_changed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stats_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", foreign_keys=[repository_id])
    file_changes: Mapped[list["FileChangeRecord"]] = relationship(
        "FileChangeRecord",
        back_populates="commit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FileChangeRecord(Base, TimestampMixin, OrgScopedMixin):
    """File modification diff record within a commit."""

    __tablename__ = "file_changes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"fch_{uuid.uuid4().hex[:16]}",
    )
    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("commits.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    previous_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    change_type: Mapped[str] = mapped_column(String(32), default="modified", nullable=False)
    insertions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deletions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    patch: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    complexity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    commit: Mapped[Optional["CommitRecord"]] = relationship(
        "CommitRecord", back_populates="file_changes"
    )


class DependencyEdgeRecord(Base, TimestampMixin, OrgScopedMixin):
    """Import and dependency edge between source files and modules."""

    __tablename__ = "dependency_edges"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"dep_{uuid.uuid4().hex[:16]}",
    )
    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_file: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    target_module: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    target_file: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    import_type: Mapped[str] = mapped_column(String(64), default="import", nullable=False)
    is_external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edge_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class AnalysisRun(Base, TimestampMixin, OrgScopedMixin):
    """Aggregated static analysis run for a commit/branch."""

    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"ana_{uuid.uuid4().hex[:16]}",
    )
    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    branch: Mapped[str] = mapped_column(String(128), default="main", nullable=False)
    job_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("execution_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    languages_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    complexity_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    test_inventory: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    coverage_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    dependency_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", foreign_keys=[repository_id])
    job: Mapped[Optional["ExecutionJob"]] = relationship("ExecutionJob", foreign_keys=[job_id])
