"""Treatments applied to plant-health issues."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from plant_health.database.models.health import HealthIssue


class TreatmentStatus(StrEnum):
    """Current state of a treatment course."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STOPPED = "stopped"
    CANCELLED = "cancelled"


class TreatmentOutcome(StrEnum):
    """Observed result of a treatment."""

    NOT_ASSESSED = "not_assessed"
    NO_CHANGE = "no_change"
    IMPROVED = "improved"
    RESOLVED = "resolved"
    WORSENED = "worsened"
    ADVERSE_REACTION = "adverse_reaction"


class Treatment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A treatment course associated with one plant-health issue."""

    __tablename__ = "treatments"
    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="valid_treatment_dates",
        ),
        CheckConstraint(
            "outcome_assessed_at IS NULL "
            "OR outcome_assessed_at >= started_at",
            name="valid_treatment_outcome_date",
        ),
    )

    health_issue_id: Mapped[UUID] = mapped_column(
        ForeignKey("health_issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    performed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    treatment_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    status: Mapped[TreatmentStatus] = mapped_column(
        Enum(
            TreatmentStatus,
            name="treatment_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=TreatmentStatus.PLANNED,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    product_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    application_method: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    dosage_description: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
    frequency_description: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
    outcome: Mapped[TreatmentOutcome] = mapped_column(
        Enum(
            TreatmentOutcome,
            name="treatment_outcome",
            native_enum=False,
            validate_strings=True,
        ),
        default=TreatmentOutcome.NOT_ASSESSED,
        nullable=False,
    )
    outcome_assessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    outcome_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    health_issue: Mapped[HealthIssue] = relationship()