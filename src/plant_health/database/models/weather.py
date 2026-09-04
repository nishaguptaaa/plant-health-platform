"""Site-level weather snapshots."""

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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from plant_health.database.models.site import Site


class WeatherRecordType(StrEnum):
    """Whether weather data is observed, forecast, or historical."""

    OBSERVED = "observed"
    FORECAST = "forecast"
    HISTORICAL = "historical"


class WeatherCondition(StrEnum):
    """Standardized description of general weather conditions."""

    CLEAR = "clear"
    MOSTLY_CLEAR = "mostly_clear"
    PARTLY_CLOUDY = "partly_cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    FREEZING_RAIN = "freezing_rain"
    SNOW = "snow"
    THUNDERSTORM = "thunderstorm"
    UNKNOWN = "unknown"


class WeatherSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Weather conditions associated with a site and point in time."""

    __tablename__ = "weather_snapshots"
    __table_args__ = (
        CheckConstraint(
            "relative_humidity_pct IS NULL "
            "OR relative_humidity_pct BETWEEN 0 AND 100",
            name="valid_weather_humidity",
        ),
        CheckConstraint(
            "cloud_cover_pct IS NULL OR cloud_cover_pct BETWEEN 0 AND 100",
            name="valid_weather_cloud_cover",
        ),
        CheckConstraint(
            "precipitation_probability_pct IS NULL "
            "OR precipitation_probability_pct BETWEEN 0 AND 100",
            name="valid_precipitation_probability",
        ),
        CheckConstraint(
            "precipitation_mm IS NULL OR precipitation_mm >= 0",
            name="valid_weather_precipitation",
        ),
        CheckConstraint(
            "wind_speed_kph IS NULL OR wind_speed_kph >= 0",
            name="valid_weather_wind_speed",
        ),
        CheckConstraint(
            "wind_direction_degrees IS NULL "
            "OR wind_direction_degrees BETWEEN 0 AND 359",
            name="valid_weather_wind_direction",
        ),
        CheckConstraint(
            "solar_radiation_w_m2 IS NULL OR solar_radiation_w_m2 >= 0",
            name="valid_solar_radiation",
        ),
        CheckConstraint(
            "uv_index IS NULL OR uv_index >= 0",
            name="valid_weather_uv_index",
        ),
    )

    site_id: Mapped[UUID] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    record_type: Mapped[WeatherRecordType] = mapped_column(
        Enum(
            WeatherRecordType,
            name="weather_record_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    provider_weather_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    condition: Mapped[WeatherCondition] = mapped_column(
        Enum(
            WeatherCondition,
            name="weather_condition",
            native_enum=False,
            validate_strings=True,
        ),
        default=WeatherCondition.UNKNOWN,
        nullable=False,
    )
    is_daylight: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    temperature_c: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    apparent_temperature_c: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    relative_humidity_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    cloud_cover_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    precipitation_probability_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    precipitation_mm: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    wind_speed_kph: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )
    wind_direction_degrees: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    surface_pressure_hpa: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )
    solar_radiation_w_m2: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )
    uv_index: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    site: Mapped[Site] = relationship()