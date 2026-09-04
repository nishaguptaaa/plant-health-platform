"""Site and geographic-context models."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from plant_health.database.models.identity import Household


class SiteType(StrEnum):
    """Kinds of physical locations that may contain plants."""

    HOUSE = "house"
    APARTMENT = "apartment"
    GREENHOUSE = "greenhouse"
    OFFICE = "office"
    OTHER = "other"


class TerrainPosition(StrEnum):
    """A site's broad position within the surrounding terrain."""

    VALLEY = "valley"
    FLAT = "flat"
    SLOPE = "slope"
    HILLTOP = "hilltop"
    UNKNOWN = "unknown"


class Site(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A property or address where household plants may live."""

    __tablename__ = "sites"
    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="valid_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="valid_longitude",
        ),
        CheckConstraint(
            "elevation_m IS NULL OR elevation_m BETWEEN -500 AND 9000",
            name="valid_elevation",
        ),
        CheckConstraint(
            "terrain_slope_degrees IS NULL "
            "OR terrain_slope_degrees BETWEEN 0 AND 90",
            name="valid_terrain_slope",
        ),
        CheckConstraint(
            "weather_sync_interval_minutes >= 15",
            name="valid_weather_sync_interval",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    site_type: Mapped[SiteType] = mapped_column(
        Enum(
            SiteType,
            name="site_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    address_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )
    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )
    elevation_m: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    terrain_position: Mapped[TerrainPosition] = mapped_column(
        Enum(
            TerrainPosition,
            name="terrain_position",
            native_enum=False,
            validate_strings=True,
        ),
        default=TerrainPosition.UNKNOWN,
        nullable=False,
    )
    terrain_slope_degrees: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    weather_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    weather_provider: Mapped[str] = mapped_column(
        String(50),
        default="open_meteo",
        nullable=False,
    )
    weather_sync_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    household: Mapped[Household] = relationship()