"""Tests for site-level weather snapshots."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    WeatherCondition,
    WeatherRecordType,
    WeatherSnapshot,
)


def test_weather_snapshot_records_site_conditions() -> None:
    """A snapshot should retain weather and solar measurements."""

    measured_at = datetime.now(UTC)

    snapshot = WeatherSnapshot(
        site_id=uuid4(),
        measured_at=measured_at,
        retrieved_at=measured_at,
        record_type=WeatherRecordType.OBSERVED,
        provider_name="Open-Meteo",
        provider_weather_code="2",
        condition=WeatherCondition.PARTLY_CLOUDY,
        is_daylight=True,
        temperature_c=Decimal("22.50"),
        relative_humidity_pct=Decimal("61.00"),
        cloud_cover_pct=Decimal("45.00"),
        precipitation_mm=Decimal("0.00"),
        solar_radiation_w_m2=Decimal("385.40"),
    )

    assert snapshot.measured_at == measured_at
    assert snapshot.condition == WeatherCondition.PARTLY_CLOUDY
    assert snapshot.temperature_c == Decimal("22.50")
    assert snapshot.cloud_cover_pct == Decimal("45.00")
    assert snapshot.solar_radiation_w_m2 == Decimal("385.40")


def test_weather_snapshot_has_validation_constraints() -> None:
    """Percentages, precipitation, wind, and sunlight should be constrained."""

    constraint_names = {
        constraint.name
        for constraint in WeatherSnapshot.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_weather_snapshots_valid_weather_humidity" in constraint_names
    assert "ck_weather_snapshots_valid_weather_cloud_cover" in constraint_names
    assert (
        "ck_weather_snapshots_valid_precipitation_probability"
        in constraint_names
    )
    assert "ck_weather_snapshots_valid_weather_precipitation" in constraint_names
    assert "ck_weather_snapshots_valid_solar_radiation" in constraint_names