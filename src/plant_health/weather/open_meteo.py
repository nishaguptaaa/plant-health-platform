"""Open-Meteo weather-provider implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from plant_health.database.models.weather import WeatherCondition
from plant_health.weather.provider import (
    WeatherProviderError,
    WeatherReading,
)

CURRENT_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "is_day",
    "precipitation",
    "precipitation_probability",
    "weather_code",
    "cloud_cover",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "shortwave_radiation",
    "uv_index",
)


def _to_decimal(value: Any) -> Decimal | None:
    """Convert a numeric API value to a decimal without float artifacts."""

    if value is None:
        return None

    return Decimal(str(value))


def _weather_condition(code: int | None) -> WeatherCondition:
    """Convert a WMO weather code into a standardized condition."""

    if code is None:
        return WeatherCondition.UNKNOWN
    if code == 0:
        return WeatherCondition.CLEAR
    if code == 1:
        return WeatherCondition.MOSTLY_CLEAR
    if code == 2:
        return WeatherCondition.PARTLY_CLOUDY
    if code == 3:
        return WeatherCondition.OVERCAST
    if code in {45, 48}:
        return WeatherCondition.FOG
    if code in {51, 53, 55}:
        return WeatherCondition.DRIZZLE
    if code in {56, 57, 66, 67}:
        return WeatherCondition.FREEZING_RAIN
    if code in {61, 63, 65, 80, 81, 82}:
        return WeatherCondition.RAIN
    if code in {71, 73, 75, 77, 85, 86}:
        return WeatherCondition.SNOW
    if code in {95, 96, 99}:
        return WeatherCondition.THUNDERSTORM

    return WeatherCondition.UNKNOWN


class OpenMeteoProvider:
    """Retrieve current weather from the Open-Meteo forecast API."""

    provider_name = "Open-Meteo"
    base_url = "https://api.open-meteo.com/v1/forecast"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Create a provider with an optional injectable HTTP client."""

        self._client = client or httpx.Client()
        self._timeout_seconds = timeout_seconds

    def fetch_current(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        elevation_m: float | None = None,
    ) -> WeatherReading:
        """Retrieve and standardize current weather conditions."""

        params: dict[str, str | float] = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "timeformat": "unixtime",
            "current": ",".join(CURRENT_VARIABLES),
            "forecast_days": 1,
        }

        if elevation_m is not None:
            params["elevation"] = elevation_m

        try:
            response = self._client.get(
                self.base_url,
                params=params,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise WeatherProviderError(
                "Open-Meteo weather request failed."
            ) from error

        return self._parse_current(payload)

    def _parse_current(self, payload: Any) -> WeatherReading:
        """Convert an Open-Meteo response into a provider-independent reading."""

        if not isinstance(payload, dict):
            raise WeatherProviderError("Open-Meteo returned an invalid response.")

        current = payload.get("current")

        if not isinstance(current, dict):
            raise WeatherProviderError(
                "Open-Meteo response did not contain current weather."
            )

        try:
            measured_at = datetime.fromtimestamp(
                float(current["time"]),
                tz=UTC,
            )
        except (KeyError, TypeError, ValueError, OSError) as error:
            raise WeatherProviderError(
                "Open-Meteo returned an invalid measurement time."
            ) from error

        weather_code_value = current.get("weather_code")
        weather_code = (
            int(weather_code_value)
            if weather_code_value is not None
            else None
        )

        is_day_value = current.get("is_day")
        is_daylight = (
            bool(is_day_value)
            if is_day_value is not None
            else None
        )

        wind_direction_value = current.get("wind_direction_10m")
        wind_direction = (
            int(wind_direction_value)
            if wind_direction_value is not None
            else None
        )

        return WeatherReading(
            provider_name=self.provider_name,
            measured_at=measured_at,
            retrieved_at=datetime.now(UTC),
            provider_weather_code=(
                str(weather_code)
                if weather_code is not None
                else None
            ),
            condition=_weather_condition(weather_code),
            is_daylight=is_daylight,
            temperature_c=_to_decimal(current.get("temperature_2m")),
            apparent_temperature_c=_to_decimal(
                current.get("apparent_temperature")
            ),
            relative_humidity_pct=_to_decimal(
                current.get("relative_humidity_2m")
            ),
            cloud_cover_pct=_to_decimal(current.get("cloud_cover")),
            precipitation_probability_pct=_to_decimal(
                current.get("precipitation_probability")
            ),
            precipitation_mm=_to_decimal(current.get("precipitation")),
            wind_speed_kph=_to_decimal(current.get("wind_speed_10m")),
            wind_direction_degrees=wind_direction,
            surface_pressure_hpa=_to_decimal(
                current.get("surface_pressure")
            ),
            solar_radiation_w_m2=_to_decimal(
                current.get("shortwave_radiation")
            ),
            uv_index=_to_decimal(current.get("uv_index")),
        )