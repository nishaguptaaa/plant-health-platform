"""Plant care event records."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
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


class CareEventType(StrEnum):
    """Kinds of care performed for a plant."""

    WATERING = "watering"
    WATER_CHANGE = "water_change"
    WATER_TOP_OFF = "water_top_off"
    FERTILIZING = "fertilizing"
    REPOTTING = "repotting"
    PRUNING = "pruning"
    CLEANING = "cleaning"
    ROTATING = "rotating"
    PEST_TREATMENT = "pest_treatment"
    PROPAGATION = "propagation"
    MISTING = "misting"
    OTHER = "other"


class CareEventSource(StrEnum):
    """Origin of a recorded care event."""

    MANUAL = "manual"
    NLP_ASSISTANT = "nlp_assistant"
    AUTOMATED = "automated"
    IMPORTED = "imported"


class WateringMethod(StrEnum):
    """How water was applied during a watering-related care event."""

    TOP = "top"
    BOTTOM = "bottom"


class CareEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A timestamped care action performed for one plant."""

    __tablename__ = "care_events"
    __table_args__ = (
        CheckConstraint(
            "amount_ml IS NULL OR amount_ml >= 0",
            name="valid_care_amount",
        ),
        CheckConstraint(
            "water_ph IS NULL OR water_ph BETWEEN 0 AND 14",
            name="valid_water_ph",
        ),
        CheckConstraint(
            "water_ec_ms_cm IS NULL OR water_ec_ms_cm >= 0",
            name="valid_water_ec",
        ),
        CheckConstraint(
            "fertilizer_dilution_ratio IS NULL "
            "OR fertilizer_dilution_ratio > 0",
            name="valid_fertilizer_dilution",
        ),
    )

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    performed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    event_type: Mapped[CareEventType] = mapped_column(
        Enum(
            CareEventType,
            name="care_event_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    source: Mapped[CareEventSource] = mapped_column(
        Enum(
            CareEventSource,
            name="care_event_source",
            native_enum=False,
            validate_strings=True,
        ),
        default=CareEventSource.MANUAL,
        nullable=False,
    )
    watering_method: Mapped[WateringMethod | None] = mapped_column(
        Enum(
            WateringMethod,
            name="watering_method",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=True,
    )
    amount_ml: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    fertilizer_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    fertilizer_dilution_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    water_ph: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    water_ec_ms_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 3),
        nullable=True,
    )
    product_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plant: Mapped[Plant] = relationship()
