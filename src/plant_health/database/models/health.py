"""Plant health issue records."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
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
    from plant_health.database.models.plant import Plant


class HealthIssueCategory(StrEnum):
    """Broad categories of plant-health problems."""

    PEST = "pest"
    DISEASE = "disease"
    ROOT_PROBLEM = "root_problem"
    NUTRIENT_PROBLEM = "nutrient_problem"
    WATERING_PROBLEM = "watering_problem"
    LIGHT_PROBLEM = "light_problem"
    TEMPERATURE_PROBLEM = "temperature_problem"
    HUMIDITY_PROBLEM = "humidity_problem"
    PHYSICAL_DAMAGE = "physical_damage"
    UNKNOWN = "unknown"
    OTHER = "other"


class HealthIssueStatus(StrEnum):
    """Current state of a plant-health issue."""

    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    MONITORING = "monitoring"
    TREATING = "treating"
    RESOLVED = "resolved"
    CHRONIC = "chronic"


class HealthIssueSource(StrEnum):
    """Origin of the proposed or confirmed issue."""

    MANUAL = "manual"
    PHOTO_AI = "photo_ai"
    SENSOR = "sensor"
    DERIVED = "derived"
    IMPORTED = "imported"


class HealthIssue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A health problem tracked across time for one plant."""

    __tablename__ = "health_issues"
    __table_args__ = (
        CheckConstraint(
            "severity_score IS NULL OR severity_score BETWEEN 1 AND 5",
            name="valid_health_issue_severity",
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="valid_health_issue_confidence",
        ),
        CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= detected_at",
            name="valid_health_issue_dates",
        ),
    )

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    detected_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    category: Mapped[HealthIssueCategory] = mapped_column(
        Enum(
            HealthIssueCategory,
            name="health_issue_category",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    status: Mapped[HealthIssueStatus] = mapped_column(
        Enum(
            HealthIssueStatus,
            name="health_issue_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=HealthIssueStatus.SUSPECTED,
        nullable=False,
    )
    source: Mapped[HealthIssueSource] = mapped_column(
        Enum(
            HealthIssueSource,
            name="health_issue_source",
            native_enum=False,
            validate_strings=True,
        ),
        default=HealthIssueSource.MANUAL,
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    severity_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    affected_area: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    suspected_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    diagnosis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    human_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plant: Mapped[Plant] = relationship()