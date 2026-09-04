"""Tests for the Open-Meteo weather provider."""

from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from plant_health.database.models import WeatherCondition
from plant_health.weather import (
    OpenMeteoProvider,
    WeatherProviderError,
)


def test_open_meteo_provider_parses_current_weather() -> None:
    """The provider should convert API JSON into a standard weather reading."""

    timestamp = 1_788_000_000

    def handle_request(request: httpx.Request) -> httpx.Response:
        assert request.url.params["latitude"] == "42.3"
        assert request.url.params["longitude"] == "-71.7"
        assert request.url.params["timezone"] == "America/New_York"
        assert "shortwave_radiation" in request.url.params["current"]

        return httpx.Response(
            200,
            json={
                "current": {
                    "time": timestamp,
                    "temperature_2m": 23.4,
                    "relative_humidity_2m": 62,
                    "apparent_temperature": 24.1,
                    "is_day": 1,
                    "precipitation": 0.2,
                    "precipitation_probability": 35,
                    "weather_code": 2,
                    "cloud_cover": 48,
                    "surface_pressure": 1008.5,
                    "wind_speed_10m": 12.3,
                    "wind_direction_10m": 215,
                    "shortwave_radiation": 410.6,
                    "uv_index": 4.2,
                }
            },
        )

    transport = httpx.MockTransport(handle_request)

    with httpx.Client(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)
        reading = provider.fetch_current(
            latitude=42.3,
            longitude=-71.7,
            timezone="America/New_York",
        )

    assert reading.provider_name == "Open-Meteo"
    assert reading.measured_at == datetime.fromtimestamp(timestamp, tz=UTC)
    assert reading.condition == WeatherCondition.PARTLY_CLOUDY
    assert reading.is_daylight is True
    assert reading.temperature_c == Decimal("23.4")
    assert reading.cloud_cover_pct == Decimal(48)
    assert reading.solar_radiation_w_m2 == Decimal("410.6")


def test_open_meteo_provider_converts_http_errors() -> None:
    """HTTP failures should become a provider-independent application error."""

    def handle_request(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={"error": True, "reason": "Service unavailable"},
        )

    transport = httpx.MockTransport(handle_request)

    with httpx.Client(transport=transport) as client:
        provider = OpenMeteoProvider(client=client)

        with pytest.raises(
            WeatherProviderError,
            match="Open-Meteo weather request failed",
        ):
            provider.fetch_current(
                latitude=42.3,
                longitude=-71.7,
            )