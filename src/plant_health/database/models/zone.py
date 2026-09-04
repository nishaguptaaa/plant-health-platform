"""Environmental zones within rooms and other spaces."""

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from plant_health.database.models.space import Space


class ZoneType(StrEnum):
    """Kinds of physical plant-placement areas within a space."""

    WINDOWSILL = "windowsill"
    TABLE = "table"
    SHELF = "shelf"
    PLANT_STAND = "plant_stand"
    FLOOR = "floor"
    HANGING = "hanging"
    BENCH = "bench"
    ROOM_CENTER = "room_center"
    OUTDOOR = "outdoor"
    OTHER = "other"


class ObstructionLevel(StrEnum):
    """How strongly surrounding objects block light from reaching a zone."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"


class EnvironmentalZone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A specific microenvironment where plants can be placed."""

    __tablename__ = "environmental_zones"
    __table_args__ = (
        UniqueConstraint(
            "space_id",
            "name",
            name="zone_name_per_space",
        ),
        CheckConstraint(
            "height_above_floor_m IS NULL OR height_above_floor_m >= 0",
            name="zone_height_above_floor_nonnegative",
        ),
        CheckConstraint(
            "estimated_sky_view_pct IS NULL "
            "OR estimated_sky_view_pct BETWEEN 0 AND 100",
            name="zone_sky_view_range",
        ),
    )

    space_id: Mapped[UUID] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone_type: Mapped[ZoneType] = mapped_column(
        Enum(
            ZoneType,
            name="zone_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    height_above_floor_m: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    direct_sun_possible: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    obstruction_level: Mapped[ObstructionLevel] = mapped_column(
        Enum(
            ObstructionLevel,
            name="obstruction_level",
            native_enum=False,
            validate_strings=True,
        ),
        default=ObstructionLevel.UNKNOWN,
        nullable=False,
    )
    estimated_sky_view_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    space: Mapped[Space] = relationship()