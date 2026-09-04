"""Longitudinal plant-health observations."""

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


class ObservationType(StrEnum):
    """Reasons a plant observation was recorded."""

    ROUTINE_CHECK = "routine_check"
    HEALTH_CHECK = "health_check"
    PHOTO_ASSESSMENT = "photo_assessment"
    SENSOR_READING = "sensor_reading"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class ObservationSource(StrEnum):
    """Origin of an observation."""

    MANUAL = "manual"
    PHOTO_AI = "photo_ai"
    SENSOR = "sensor"
    DERIVED = "derived"
    IMPORTED = "imported"


class PlantObservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A timestamped snapshot of an individual plant's condition."""

    __tablename__ = "plant_observations"
    __table_args__ = (
        CheckConstraint(
            "overall_health_score IS NULL "
            "OR overall_health_score BETWEEN 0 AND 10",
            name="valid_overall_health_score",
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="valid_observation_confidence",
        ),
        CheckConstraint(
            "leaf_count IS NULL OR leaf_count >= 0",
            name="valid_leaf_count",
        ),
        CheckConstraint(
            "new_leaf_count IS NULL OR new_leaf_count >= 0",
            name="valid_new_leaf_count",
        ),
        CheckConstraint(
            "yellow_leaf_count IS NULL OR yellow_leaf_count >= 0",
            name="valid_yellow_leaf_count",
        ),
        CheckConstraint(
            "damaged_leaf_count IS NULL OR damaged_leaf_count >= 0",
            name="valid_damaged_leaf_count",
        ),
        CheckConstraint(
            "height_cm IS NULL OR height_cm >= 0",
            name="valid_plant_height",
        ),
        CheckConstraint(
            "canopy_width_cm IS NULL OR canopy_width_cm >= 0",
            name="valid_canopy_width",
        ),
    )

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    observation_type: Mapped[ObservationType] = mapped_column(
        Enum(
            ObservationType,
            name="observation_type",
            native_enum=False,
            validate_strings=True,
        ),
        default=ObservationType.ROUTINE_CHECK,
        nullable=False,
    )
    source: Mapped[ObservationSource] = mapped_column(
        Enum(
            ObservationSource,
            name="observation_source",
            native_enum=False,
            validate_strings=True,
        ),
        default=ObservationSource.MANUAL,
        nullable=False,
    )
    source_detail: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    overall_health_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    leaf_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    new_leaf_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    yellow_leaf_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    damaged_leaf_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    height_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )
    canopy_width_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )
    visible_pests: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    flowering: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
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

    plant: Mapped[Plant] = relationship()