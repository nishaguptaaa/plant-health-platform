"""Lifecycle and location history for individual plants."""

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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utc_now,
)
from plant_health.database.models.plant import PlantStatus

if TYPE_CHECKING:
    from plant_health.database.models.plant import Plant
    from plant_health.database.models.zone import EnvironmentalZone


class LifecycleEventType(StrEnum):
    """Important events during a plant's life."""

    ACQUIRED = "acquired"
    PROPAGATED = "propagated"
    STATUS_CHANGED = "status_changed"
    DORMANCY_STARTED = "dormancy_started"
    DORMANCY_ENDED = "dormancy_ended"
    QUARANTINED = "quarantined"
    RECOVERED = "recovered"
    TRANSFERRED = "transferred"
    DECEASED = "deceased"
    OTHER = "other"


class LocationChangeReason(StrEnum):
    """Why a plant was placed in or moved to a zone."""

    INITIAL_PLACEMENT = "initial_placement"
    LIGHT_ADJUSTMENT = "light_adjustment"
    SEASONAL_MOVE = "seasonal_move"
    QUARANTINE = "quarantine"
    REPOTTING = "repotting"
    HOUSE_MOVE = "house_move"
    CARETAKER_TRANSFER = "caretaker_transfer"
    OTHER = "other"


class PlantLifecycleEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A dated event in an individual plant's lifecycle."""

    __tablename__ = "plant_lifecycle_events"

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[LifecycleEventType] = mapped_column(
        Enum(
            LifecycleEventType,
            name="lifecycle_event_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    status_after: Mapped[PlantStatus | None] = mapped_column(
        Enum(
            PlantStatus,
            name="plant_status",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plant: Mapped[Plant] = relationship()


class PlantLocationHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A period when a plant was located in one environmental zone."""

    __tablename__ = "plant_location_history"
    __table_args__ = (
        UniqueConstraint(
            "plant_id",
            "started_at",
            name="plant_location_start_per_plant",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="plant_location_end_after_start",
        ),
    )

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    zone_id: Mapped[UUID] = mapped_column(
        ForeignKey("environmental_zones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reason: Mapped[LocationChangeReason] = mapped_column(
        Enum(
            LocationChangeReason,
            name="location_change_reason",
            native_enum=False,
            validate_strings=True,
        ),
        default=LocationChangeReason.OTHER,
        nullable=False,
    )
    placement_label: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plant: Mapped[Plant] = relationship()
    zone: Mapped[EnvironmentalZone] = relationship()