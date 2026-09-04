"""Growing methods used for individual plants."""

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
    utc_now,
)

if TYPE_CHECKING:
    from plant_health.database.models.plant import Plant


class GrowingMethodType(StrEnum):
    """Ways a plant's roots may be cultivated."""

    SOIL_BASED = "soil_based"
    SOILLESS_MIX = "soilless_mix"
    ORCHID_BARK = "orchid_bark"
    SPHAGNUM_MOSS = "sphagnum_moss"
    SEMI_HYDRO_LECA = "semi_hydro_leca"
    SEMI_HYDRO_PON = "semi_hydro_pon"
    FULL_WATER_CULTURE = "full_water_culture"
    WATER_PROPAGATION = "water_propagation"
    MOUNTED = "mounted"
    BARE_ROOT_AIR = "bare_root_air"
    OTHER = "other"


class PlantCultivationHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A period when a plant used a particular growing method."""

    __tablename__ = "plant_cultivation_history"
    __table_args__ = (
        UniqueConstraint(
            "plant_id",
            "started_at",
            name="plant_cultivation_start_per_plant",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="plant_cultivation_end_after_start",
        ),
        CheckConstraint(
            "root_submersion_percent IS NULL "
            "OR root_submersion_percent BETWEEN 0 AND 100",
            name="plant_cultivation_root_submersion_range",
        ),
        CheckConstraint(
            "reservoir_target_depth_cm IS NULL "
            "OR reservoir_target_depth_cm >= 0",
            name="plant_cultivation_reservoir_depth_nonnegative",
        ),
    )

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method_type: Mapped[GrowingMethodType] = mapped_column(
        Enum(
            GrowingMethodType,
            name="growing_method_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    custom_method_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
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

    root_submersion_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    reservoir_target_depth_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    is_experimental: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plant: Mapped[Plant] = relationship()