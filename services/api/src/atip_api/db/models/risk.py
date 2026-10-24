"""Risk assessment and defect prediction database models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atip_api.db.base import Base, OrgScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from atip_api.db.models.repository import Repository


class RiskAssessment(Base, TimestampMixin, OrgScopedMixin):
    """Persisted versioned risk assessment for a repository commit or PR snapshot."""

    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"rsk_{uuid.uuid4().hex[:16]}",
    )
    repository_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    branch: Mapped[str] = mapped_column(String(128), default="main", nullable=False)

    # Model provenance and version
    model_version: Mapped[str] = mapped_column(String(64), default="deterministic-v1.0.0", nullable=False)
    model_type: Mapped[str] = mapped_column(String(32), default="deterministic", nullable=False) # deterministic or predictive_ml

    # Scores & classifications
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(32), nullable=False) # low, medium, high, critical
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    has_missing_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Explainable weights, file assessments & summary breakdown
    feature_weights: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    file_assessments: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    summary_stats: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Optional execution / analysis links
    analysis_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", foreign_keys=[repository_id])
