"""ExecutionJob entity and state machine enums."""

import enum
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atip_api.db.base import Base, OrgScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from atip_api.db.models.repository import Repository


class JobType(str, enum.Enum):
    REPO_MINING = "repo_mining"
    RISK_ASSESSMENT = "risk_assessment"
    WHITEBOX_ANALYSIS = "whitebox_analysis"
    TEST_GENERATION = "test_generation"
    SANDBOX_EXECUTION = "sandbox_execution"
    MUTATION_ANALYSIS = "mutation_analysis"
    FAILURE_INVESTIGATION = "failure_investigation"
    REPORT_GENERATION = "report_generation"


class JobStatus(str, enum.Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    COLLECTING = "collecting"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ExecutionJob(Base, TimestampMixin, OrgScopedMixin):
    __tablename__ = "execution_jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"job_{uuid.uuid4().hex[:16]}",
    )
    repository_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=32),
        default=JobStatus.CREATED,
        nullable=False,
        index=True,
    )
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    repository: Mapped[Optional["Repository"]] = relationship(
        "Repository", back_populates="jobs", lazy="selectin"
    )
