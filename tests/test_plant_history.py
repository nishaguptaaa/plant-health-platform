"""Tests for plant lifecycle and location history."""

from datetime import UTC, datetime

from plant_health.database import Base, create_database_engine, create_session_factory
from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    LifecycleEventType,
    LocationChangeReason,
    Plant,
    PlantLifecycleEvent,
    PlantLocationHistory,
    PlantStatus,
    Site,
    SiteType,
    Space,
    SpaceType,
    ZoneType,
)


def test_plant_keeps_location_and_lifecycle_history() -> None:
    """A plant should retain old locations and important life events."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Test Household")
        site = Site(
            household=household,
            name="Test Home",
            site_type=SiteType.HOUSE,
            timezone="America/New_York",
        )
        space = Space(
            site=site,
            name="Living Room",
            space_type=SpaceType.ROOM,
        )
        first_zone = EnvironmentalZone(
            space=space,
            name="Window Table",
            zone_type=ZoneType.TABLE,
        )
        second_zone = EnvironmentalZone(
            space=space,
            name="Plant Stand",
            zone_type=ZoneType.PLANT_STAND,
        )
        plant = Plant(
            household=household,
            plant_code="P001",
            nickname="Test Plant",
        )

        move_date = datetime(2027, 6, 1, tzinfo=UTC)
        first_location = PlantLocationHistory(
            plant=plant,
            zone=first_zone,
            started_at=datetime(2026, 9, 1, tzinfo=UTC),
            ended_at=move_date,
            reason=LocationChangeReason.INITIAL_PLACEMENT,
        )
        current_location = PlantLocationHistory(
            plant=plant,
            zone=second_zone,
            started_at=move_date,
            reason=LocationChangeReason.LIGHT_ADJUSTMENT,
        )
        lifecycle_event = PlantLifecycleEvent(
            plant=plant,
            event_type=LifecycleEventType.STATUS_CHANGED,
            occurred_at=move_date,
            status_after=PlantStatus.ACTIVE,
            description="Plant returned to active growth.",
        )

        session.add_all([first_location, current_location, lifecycle_event])
        session.commit()

        assert first_location.plant_id == current_location.plant_id
        assert first_location.zone_id != current_location.zone_id
        assert first_location.ended_at == current_location.started_at
        assert current_location.ended_at is None
        assert lifecycle_event.plant_id == plant.id