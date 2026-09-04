"""Indoor environmental and light measurements."""

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
    from plant_health.database.models.identity import User
    from plant_health.database.models.light import LightSource
    from plant_health.database.models.plant import Plant
    from plant_health.database.models.zone import EnvironmentalZone


class MeasurementSource(StrEnum):
    """How an environmental measurement was obtained."""

    MANUAL_METER = "manual_meter"
    PHONE_SENSOR = "phone_sensor"
    PHYSICAL_SENSOR = "physical_sensor"
    IMPORTED = "imported"
    DERIVED = "derived"


class LightMeasurementContext(StrEnum):
    """Location or lighting situation represented by a light reading."""

    AMBIENT_ZONE = "ambient_zone"
    PLANT_LEAF_LEVEL = "plant_leaf_level"
    AT_LIGHT_SOURCE = "at_light_source"
    DIRECT_SUN = "direct_sun"
    GROW_LIGHT_ONLY = "grow_light_only"
    MIXED_LIGHT = "mixed_light"
    UNKNOWN = "unknown"


class EnvironmentalMeasurement(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """A timestamped measurement within a plant-placement zone."""

    __tablename__ = "environmental_measurements"
    __table_args__ = (
        CheckConstraint(
            "lux IS NOT NULL "
            "OR ppfd_umol_m2_s IS NOT NULL "
            "OR dli_mol_m2_day IS NOT NULL "
            "OR temperature_c IS NOT NULL "
            "OR relative_humidity_pct IS NOT NULL "
            "OR soil_moisture_pct IS NOT NULL "
            "OR water_temperature_c IS NOT NULL "
            "OR water_ph IS NOT NULL "
            "OR water_ec_ms_cm IS NOT NULL",
            name="measurement_has_value",
        ),
        CheckConstraint(
            "lux IS NULL OR lux >= 0",
            name="valid_measurement_lux",
        ),
        CheckConstraint(
            "ppfd_umol_m2_s IS NULL OR ppfd_umol_m2_s >= 0",
            name="valid_measurement_ppfd",
        ),
        CheckConstraint(
            "dli_mol_m2_day IS NULL OR dli_mol_m2_day >= 0",
            name="valid_measurement_dli",
        ),
        CheckConstraint(
            "relative_humidity_pct IS NULL "
            "OR relative_humidity_pct BETWEEN 0 AND 100",
            name="valid_measurement_humidity",
        ),
        CheckConstraint(
            "soil_moisture_pct IS NULL "
            "OR soil_moisture_pct BETWEEN 0 AND 100",
            name="valid_measurement_soil_moisture",
        ),
        CheckConstraint(
            "water_ph IS NULL OR water_ph BETWEEN 0 AND 14",
            name="valid_measurement_water_ph",
        ),
        CheckConstraint(
            "water_ec_ms_cm IS NULL OR water_ec_ms_cm >= 0",
            name="valid_measurement_water_ec",
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="valid_measurement_confidence",
        ),
        CheckConstraint(
            "measurement_duration_seconds IS NULL "
            "OR measurement_duration_seconds > 0",
            name="valid_measurement_duration",
        ),
    )

    zone_id: Mapped[UUID] = mapped_column(
        ForeignKey("environmental_zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    light_source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("light_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    source: Mapped[MeasurementSource] = mapped_column(
        Enum(
            MeasurementSource,
            name="measurement_source",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    light_context: Mapped[LightMeasurementContext | None] = mapped_column(
        Enum(
            LightMeasurementContext,
            name="light_measurement_context",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=True,
    )
    device_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )
    measurement_duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    lux: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    ppfd_umol_m2_s: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    dli_mol_m2_day: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )
    temperature_c: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    relative_humidity_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    soil_moisture_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    water_temperature_c: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
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
    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    zone: Mapped[EnvironmentalZone] = relationship()
    plant: Mapped[Plant | None] = relationship()
    light_source: Mapped[LightSource | None] = relationship()
    recorded_by_user: Mapped[User | None] = relationship()