"""Shared interface and data structure for weather providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from plant_health.database.models.weather import WeatherCondition


class WeatherProviderError(RuntimeError):
    """Raised when weather data cannot be retrieved or interpreted."""


@dataclass(frozen=True, slots=True)
class WeatherReading:
    """Provider-independent current weather data."""

    provider_name: str
    measured_at: datetime
    retrieved_at: datetime
    provider_weather_code: str | None
    condition: WeatherCondition
    is_daylight: bool | None
    temperature_c: Decimal | None
    apparent_temperature_c: Decimal | None
    relative_humidity_pct: Decimal | None
    cloud_cover_pct: Decimal | None
    precipitation_probability_pct: Decimal | None
    precipitation_mm: Decimal | None
    wind_speed_kph: Decimal | None
    wind_direction_degrees: int | None
    surface_pressure_hpa: Decimal | None
    solar_radiation_w_m2: Decimal | None
    uv_index: Decimal | None


class WeatherProvider(Protocol):
    """Behavior required from every weather provider."""

    provider_name: str

    def fetch_current(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        elevation_m: float | None = None,
    ) -> WeatherReading:
        """Retrieve current weather for one geographical location."""