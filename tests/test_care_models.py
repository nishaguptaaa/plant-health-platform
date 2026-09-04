"""Tests for plant care events."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    CareEvent,
    CareEventSource,
    CareEventType,
)


def test_care_event_records_watering() -> None:
    """A watering event should retain structured care details."""

    plant_id = uuid4()
    occurred_at = datetime.now(UTC)

    event = CareEvent(
        plant_id=plant_id,
        occurred_at=occurred_at,
        event_type=CareEventType.WATERING,
        source=CareEventSource.MANUAL,
        amount_ml=Decimal("500.00"),
        water_ph=Decimal("6.50"),
        notes="Watered thoroughly and allowed excess water to drain.",
    )

    assert event.plant_id == plant_id
    assert event.occurred_at == occurred_at
    assert event.event_type == CareEventType.WATERING
    assert event.amount_ml == Decimal("500.00")
    assert event.water_ph == Decimal("6.50")


def test_care_event_has_validation_constraints() -> None:
    """Water and fertilizer measurements should be constrained."""

    constraint_names = {
        constraint.name
        for constraint in CareEvent.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_care_events_valid_care_amount" in constraint_names
    assert "ck_care_events_valid_water_ph" in constraint_names
    assert "ck_care_events_valid_water_ec" in constraint_names
    assert "ck_care_events_valid_fertilizer_dilution" in constraint_names