"""Tests for retrieving and saving site weather."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from plant_health.database.models import (
    Site,
    SiteType,
    WeatherCondition,
    WeatherSnapshot,
)
from plant_health.weather import (
    WeatherCaptureError,
    WeatherReading,
    capture_current_weather,
)


def test_capture_current_weather_saves_snapshot() -> None:
    """Current provider data should be converted and saved."""

    captured_at = datetime.now(UTC)
    site = Site(
        id=uuid4(),
        household_id=uuid4(),
        name="Test Home",
        site_type=SiteType.HOUSE,
        latitude=Decimal("42.300000"),
        longitude=Decimal("-71.700000"),
        elevation_m=Decimal("120.50"),
        timezone="America/New_York",
        weather_enabled=True,
    )
    reading = WeatherReading(
        provider_name="Test Provider",
        measured_at=captured_at,
        retrieved_at=captured_at,
        provider_weather_code="2",
        condition=WeatherCondition.PARTLY_CLOUDY,
        is_daylight=True,
        temperature_c=Decimal("22.50"),
        apparent_temperature_c=Decimal("23.10"),
        relative_humidity_pct=Decimal("60.00"),
        cloud_cover_pct=Decimal("45.00"),
        precipitation_probability_pct=Decimal("20.00"),
        precipitation_mm=Decimal("0.00"),
        wind_speed_kph=Decimal("8.50"),
        wind_direction_degrees=180,
        surface_pressure_hpa=Decimal("1009.50"),
        solar_radiation_w_m2=Decimal("390.00"),
        uv_index=Decimal("4.10"),
    )

    session = Mock(spec=Session)
    provider = Mock()
    provider.fetch_current.return_value = reading

    snapshot = capture_current_weather(
        session,
        site=site,
        provider=provider,
    )

    provider.fetch_current.assert_called_once_with(
        latitude=42.3,
        longitude=-71.7,
        timezone="America/New_York",
        elevation_m=120.5,
    )
    session.add.assert_called_once_with(snapshot)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(snapshot)

    assert isinstance(snapshot, WeatherSnapshot)
    assert snapshot.site_id == site.id
    assert snapshot.condition == WeatherCondition.PARTLY_CLOUDY
    assert snapshot.solar_radiation_w_m2 == Decimal("390.00")


def test_capture_current_weather_requires_coordinates() -> None:
    """Weather should not be requested without site coordinates."""

    site = Site(
        id=uuid4(),
        household_id=uuid4(),
        name="Site Without Coordinates",
        site_type=SiteType.HOUSE,
        latitude=None,
        longitude=None,
        timezone="America/New_York",
        weather_enabled=True,
    )

    session = Mock(spec=Session)
    provider = Mock()

    with pytest.raises(
        WeatherCaptureError,
        match="needs latitude and longitude",
    ):
        capture_current_weather(
            session,
            site=site,
            provider=provider,
        )

    provider.fetch_current.assert_not_called()
    session.add.assert_not_called()