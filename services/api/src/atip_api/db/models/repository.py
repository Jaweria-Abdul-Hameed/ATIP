"""GitHubInstallation, Repository, and RepositorySnapshot entities."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atip_api.db.base import Base, OrgScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from atip_api.db.models.job import ExecutionJob
    from atip_api.db.models.organization import Organization


class GitHubInstallation(Base, TimestampMixin, OrgScopedMixin):
    __tablename__ = "github_installations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"ghi_{uuid.uuid4().hex[:16]}",
    )
    installation_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    account_login: Mapped[str] = mapped_column(String(255), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), default="Organization", nullable=False)
    repository_selection: Mapped[str] = mapped_column(
        String(32), default="selected", nullable=False
    )
    permissions: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    encrypted_token: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository",
        back_populates="installation",
        cascade="all, delete-orphan",
    )


class Repository(Base, TimestampMixin, OrgScopedMixin):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"repo_{uuid.uuid4().hex[:16]}",
    )
    github_installation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("github_installations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    github_repo_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    default_branch: Mapped[str] = mapped_column(String(128), default="main", nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clone_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="repositories", lazy="selectin"
    )
    installation: Mapped[Optional["GitHubInstallation"]] = relationship(
        "GitHubInstallation", back_populates="repositories", lazy="selectin"
    )
    snapshots: Mapped[list["RepositorySnapshot"]] = relationship(
        "RepositorySnapshot",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    jobs: Mapped[list["ExecutionJob"]] = relationship(
        "ExecutionJob",
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class RepositorySnapshot(Base, TimestampMixin, OrgScopedMixin):
    __tablename__ = "repository_snapshots"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"snap_{uuid.uuid4().hex[:16]}",
    )
    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    branch_name: Mapped[str] = mapped_column(String(128), nullable=False)
    ref: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tree_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_shas: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    stats_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="snapshots")
