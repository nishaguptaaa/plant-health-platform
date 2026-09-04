"""Natural and artificial light-source models."""

from __future__ import annotations

import uuid
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from plant_health.database.models.space import Space
    from plant_health.database.models.zone import EnvironmentalZone


class LightSourceType(StrEnum):
    """Kinds of natural and artificial light sources."""

    WINDOW = "window"
    SKYLIGHT = "skylight"
    GLASS_DOOR = "glass_door"
    GROW_LIGHT = "grow_light"
    OTHER = "other"


class OrientationSource(StrEnum):
    """How an orientation measurement was obtained."""

    ESTIMATED = "estimated"
    PHONE_COMPASS = "phone_compass"
    MEASURED = "measured"
    ROOM_SCAN = "room_scan"
    UNKNOWN = "unknown"


class LightSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A window, skylight, glass door, or artificial grow light."""

    __tablename__ = "light_sources"
    __table_args__ = (
        CheckConstraint(
            "orientation_degrees IS NULL OR "
            "(orientation_degrees >= 0 AND orientation_degrees < 360)",
            name="light_source_orientation_range",
        ),
        CheckConstraint(
            "orientation_accuracy_degrees IS NULL OR "
            "orientation_accuracy_degrees >= 0",
            name="light_source_orientation_accuracy_nonnegative",
        ),
        CheckConstraint(
            "width_m IS NULL OR width_m > 0",
            name="light_source_width_positive",
        ),
        CheckConstraint(
            "height_m IS NULL OR height_m > 0",
            name="light_source_height_positive",
        ),
        CheckConstraint(
            "sill_height_m IS NULL OR sill_height_m >= 0",
            name="light_source_sill_height_nonnegative",
        ),
        CheckConstraint(
            "transmission_percent IS NULL OR "
            "(transmission_percent >= 0 AND transmission_percent <= 100)",
            name="light_source_transmission_range",
        ),
        CheckConstraint(
            "wattage_w IS NULL OR wattage_w >= 0",
            name="light_source_wattage_nonnegative",
        ),
        CheckConstraint(
            "color_temperature_k IS NULL OR color_temperature_k > 0",
            name="light_source_color_temperature_positive",
        ),
    )

    space_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[LightSourceType] = mapped_column(
        SqlEnum(
            LightSourceType,
            name="light_source_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )

    orientation_degrees: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    orientation_source: Mapped[OrientationSource] = mapped_column(
        SqlEnum(
            OrientationSource,
            name="orientation_source",
            native_enum=False,
            validate_strings=True,
        ),
        default=OrientationSource.UNKNOWN,
        nullable=False,
    )
    orientation_accuracy_degrees: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    width_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    height_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    sill_height_m: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    transmission_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    wattage_w: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )
    color_temperature_k: Mapped[int | None] = mapped_column(nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    space: Mapped[Space] = relationship()


class ZoneLightSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Connect a plant-placement zone to one contributing light source."""

    __tablename__ = "zone_light_sources"
    __table_args__ = (
        UniqueConstraint(
            "zone_id",
            "light_source_id",
            name="uq_zone_light_sources_zone_light_source",
        ),
        CheckConstraint(
            "distance_m IS NULL OR distance_m >= 0",
            name="zone_light_source_distance_nonnegative",
        ),
        CheckConstraint(
            "contribution_weight IS NULL OR "
            "(contribution_weight >= 0 AND contribution_weight <= 1)",
            name="zone_light_source_contribution_weight_range",
        ),
    )

    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("environmental_zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    light_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("light_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    distance_m: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    has_clear_line_of_sight: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    contribution_weight: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    zone: Mapped[EnvironmentalZone] = relationship()
    light_source: Mapped[LightSource] = relationship()