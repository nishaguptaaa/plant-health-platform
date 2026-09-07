"""Tests for moving plants between environmental zones."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    LocationChangeReason,
    PlantLocationHistory,
    Site,
    SiteType,
    Space,
    SpaceType,
    ZoneType,
)
from plant_health.services import (
    PlantMovementError,
    create_plant_with_location,
    load_plant_collection,
    move_plant,
)


def _create_plant_and_zones(
    session: Session,
) -> tuple[UUID, UUID, UUID, UUID]:
    """Create one plant and two available zones."""

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

    first_zone = EnvironmentalZone(
        space_id=space.id,
        name="Window Shelf",
        zone_type=ZoneType.SHELF,
    )
    second_zone = EnvironmentalZone(
        space_id=space.id,
        name="Plant Table",
        zone_type=ZoneType.TABLE,
    )
    session.add_all([first_zone, second_zone])
    session.commit()

    result = create_plant_with_location(
        session,
        household_id=household.id,
        zone_id=first_zone.id,
        nickname="Leafy",
        location_started_at=datetime(
            2026,
            1,
            1,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    return (
        household.id,
        result.plant.id,
        first_zone.id,
        second_zone.id,
    )


def test_move_plant_closes_previous_location() -> None:
    """Moving should close the old location and create a new one."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        (
            household_id,
            plant_id,
            first_zone_id,
            second_zone_id,
        ) = _create_plant_and_zones(session)

        moved_at = datetime(
            2026,
            2,
            1,
            9,
            30,
            tzinfo=UTC,
        )

        result = move_plant(
            session,
            household_id=household_id,
            plant_id=plant_id,
            new_zone_id=second_zone_id,
            reason=LocationChangeReason.LIGHT_ADJUSTMENT,
            moved_at=moved_at,
            placement_label="Right side of the table",
            notes="Moved farther away from direct afternoon sun.",
        )

        assert result.previous_location is not None
        assert result.previous_location.zone_id == first_zone_id
        assert (
            result.previous_location.ended_at.replace(tzinfo=None)
            == moved_at.replace(tzinfo=None)
        )

        assert result.new_location.zone_id == second_zone_id
        assert result.new_location.ended_at is None
        assert result.new_location.reason == (
            LocationChangeReason.LIGHT_ADJUSTMENT
        )
        assert result.new_location.placement_label == (
            "Right side of the table"
        )

        history = list(
            session.scalars(
                select(PlantLocationHistory)
                .where(
                    PlantLocationHistory.plant_id == plant_id
                )
                .order_by(PlantLocationHistory.started_at)
            ).all()
        )

        assert len(history) == 2
        assert history[0].ended_at is not None
        assert history[1].ended_at is None

        collection = load_plant_collection(
            session,
            household_ids=[household_id],
        )

        assert len(collection) == 1
        assert collection[0].zone_name == "Plant Table"


def test_move_plant_rejects_current_zone() -> None:
    """A move must select a different destination zone."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        (
            household_id,
            plant_id,
            first_zone_id,
            _,
        ) = _create_plant_and_zones(session)

        with pytest.raises(
            PlantMovementError,
            match="already in the selected zone",
        ):
            move_plant(
                session,
                household_id=household_id,
                plant_id=plant_id,
                new_zone_id=first_zone_id,
                reason=LocationChangeReason.OTHER,
            )


def test_move_plant_rejects_zone_from_another_household() -> None:
    """A plant cannot move into another household's zone."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        (
            household_id,
            plant_id,
            _,
            _,
        ) = _create_plant_and_zones(session)

        other_household = Household(name="Other Household")
        session.add(other_household)
        session.flush()

        other_site = Site(
            household_id=other_household.id,
            name="Other Home",
            site_type=SiteType.HOUSE,
            timezone="America/New_York",
            weather_enabled=False,
        )
        session.add(other_site)
        session.flush()

        other_space = Space(
            site_id=other_site.id,
            name="Other Room",
            space_type=SpaceType.ROOM,
        )
        session.add(other_space)
        session.flush()

        other_zone = EnvironmentalZone(
            space_id=other_space.id,
            name="Other Shelf",
            zone_type=ZoneType.SHELF,
        )
        session.add(other_zone)
        session.commit()

        with pytest.raises(
            PlantMovementError,
            match="does not belong to this household",
        ):
            move_plant(
                session,
                household_id=household_id,
                plant_id=plant_id,
                new_zone_id=other_zone.id,
                reason=LocationChangeReason.HOUSE_MOVE,
            )