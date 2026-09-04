"""Tests for indoor environmental measurements."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    EnvironmentalMeasurement,
    LightMeasurementContext,
    MeasurementSource,
)


def test_environmental_measurement_records_leaf_level_light() -> None:
    """A measurement should retain light and indoor conditions."""

    measured_at = datetime.now(UTC)
    zone_id = uuid4()
    plant_id = uuid4()

    measurement = EnvironmentalMeasurement(
        zone_id=zone_id,
        plant_id=plant_id,
        measured_at=measured_at,
        source=MeasurementSource.PHONE_SENSOR,
        light_context=LightMeasurementContext.PLANT_LEAF_LEVEL,
        device_name="Phone light meter",
        measurement_duration_seconds=30,
        lux=Decimal("6250.00"),
        temperature_c=Decimal("23.40"),
        relative_humidity_pct=Decimal("58.00"),
        confidence=Decimal("0.7500"),
    )

    assert measurement.zone_id == zone_id
    assert measurement.plant_id == plant_id
    assert measurement.measured_at == measured_at
    assert measurement.lux == Decimal("6250.00")
    assert measurement.relative_humidity_pct == Decimal("58.00")
    assert measurement.light_context == (
        LightMeasurementContext.PLANT_LEAF_LEVEL
    )


def test_environmental_measurement_has_validation_constraints() -> None:
    """Measurements should require data and enforce valid ranges."""

    constraint_names = {
        constraint.name
        for constraint in EnvironmentalMeasurement.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert (
        "ck_environmental_measurements_measurement_has_value"
        in constraint_names
    )
    assert (
        "ck_environmental_measurements_valid_measurement_lux"
        in constraint_names
    )
    assert (
        "ck_environmental_measurements_valid_measurement_humidity"
        in constraint_names
    )
    assert (
        "ck_environmental_measurements_valid_measurement_water_ph"
        in constraint_names
    )
    assert (
        "ck_environmental_measurements_valid_measurement_confidence"
        in constraint_names
    )