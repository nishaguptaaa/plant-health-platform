"""Tests for recording plant care events."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    CareEventSource,
    CareEventType,
    EnvironmentalZone,
    Household,
    HouseholdMembership,
    HouseholdRole,
    Site,
    SiteType,
    Space,
    SpaceType,
    User,
    ZoneType,
)
from plant_health.services import (
    CareRecordingError,
    create_plant_with_location,
    record_care_event,
)


def _create_plant(session: Session) -> tuple[UUID, UUID]:
    """Create one plant in one household, and return their IDs."""

    household = Household(name="Test Household")
    session.add(household)
    session.flush()

    site = Site(
        household_id=household.id,
        name="Test Home",
        site_type=SiteType.HOUSE,
        timezone="America/New_York",
        weather_enabled=False,
    )
    session.add(site)
    session.flush()

    space = Space(
        site_id=site.id,
        name="Living Room",
        space_type=SpaceType.ROOM,
    )
    session.add(space)
    session.flush()

    zone = EnvironmentalZone(
        space_id=space.id,
        name="Window Shelf",
        zone_type=ZoneType.SHELF,
    )
    session.add(zone)
    session.commit()

    result = create_plant_with_location(
        session,
        household_id=household.id,
        zone_id=zone.id,
        nickname="Leafy",
    )

    return household.id, result.plant.id


def test_record_care_event_saves_watering() -> None:
    """A basic watering event should be recorded successfully."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        occurred_at = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)

        care_event = record_care_event(
            session,
            household_id=household_id,
            plant_id=plant_id,
            event_type=CareEventType.WATERING,
            occurred_at=occurred_at,
            amount_ml=Decimal(250),
        )

        assert care_event.id is not None
        assert care_event.plant_id == plant_id
        assert care_event.event_type == CareEventType.WATERING
        assert care_event.source == CareEventSource.MANUAL
        assert care_event.amount_ml == Decimal("250.00")


def test_record_care_event_defaults_occurred_at_to_now() -> None:
    """Omitting the timestamp should default to the current time."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        before = datetime.now(UTC)

        care_event = record_care_event(
            session,
            household_id=household_id,
            plant_id=plant_id,
            event_type=CareEventType.MISTING,
        )

        after = datetime.now(UTC)

        assert before <= care_event.occurred_at.replace(tzinfo=UTC) <= after


def test_record_care_event_records_misting_type() -> None:
    """Misting should be storable as its own care event type."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        care_event = record_care_event(
            session,
            household_id=household_id,
            plant_id=plant_id,
            event_type=CareEventType.MISTING,
        )

        assert care_event.event_type == CareEventType.MISTING


def test_record_care_event_rejects_plant_from_another_household() -> None:
    """A care event cannot be recorded against another household's plant."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _, plant_id = _create_plant(session)

        other_household = Household(name="Other Household")
        session.add(other_household)
        session.commit()

        with pytest.raises(
            CareRecordingError,
            match="does not belong to this household",
        ):
            record_care_event(
                session,
                household_id=other_household.id,
                plant_id=plant_id,
                event_type=CareEventType.WATERING,
            )


def test_record_care_event_rejects_future_timestamp() -> None:
    """A care event cannot be recorded with a future timestamp."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        future_time = datetime.now(UTC) + timedelta(days=1)

        with pytest.raises(
            CareRecordingError,
            match="cannot be in the future",
        ):
            record_care_event(
                session,
                household_id=household_id,
                plant_id=plant_id,
                event_type=CareEventType.WATERING,
                occurred_at=future_time,
            )


def test_record_care_event_rejects_negative_amount() -> None:
    """A negative watering amount should be rejected before saving."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        with pytest.raises(
            CareRecordingError,
            match="Amount must be zero or greater",
        ):
            record_care_event(
                session,
                household_id=household_id,
                plant_id=plant_id,
                event_type=CareEventType.WATERING,
                amount_ml=Decimal(-10),
            )


def test_record_care_event_rejects_invalid_water_ph() -> None:
    """A water pH outside 0-14 should be rejected before saving."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        with pytest.raises(
            CareRecordingError,
            match="Water pH must be between 0 and 14",
        ):
            record_care_event(
                session,
                household_id=household_id,
                plant_id=plant_id,
                event_type=CareEventType.WATERING,
                water_ph=Decimal(15),
            )


def test_record_care_event_accepts_active_household_member() -> None:
    """An active household member can be recorded as who performed care."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        user = User(
            display_name="Nisha",
            email="nisha@example.com",
        )
        session.add(user)
        session.flush()

        membership = HouseholdMembership(
            household_id=household_id,
            user_id=user.id,
            role=HouseholdRole.OWNER,
        )
        session.add(membership)
        session.commit()

        care_event = record_care_event(
            session,
            household_id=household_id,
            plant_id=plant_id,
            event_type=CareEventType.WATERING,
            performed_by_user_id=user.id,
        )

        assert care_event.performed_by_user_id == user.id


def test_record_care_event_rejects_non_member_recorder() -> None:
    """A user who is not an active household member cannot be recorded."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        outsider = User(
            display_name="Outsider",
            email="outsider@example.com",
        )
        session.add(outsider)
        session.commit()

        with pytest.raises(
            CareRecordingError,
            match="not an active member of this household",
        ):
            record_care_event(
                session,
                household_id=household_id,
                plant_id=plant_id,
                event_type=CareEventType.WATERING,
                performed_by_user_id=outsider.id,
            )
