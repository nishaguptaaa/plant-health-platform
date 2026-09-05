"""Tests for the plant setup service."""

import pytest
from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    LocationChangeReason,
    Site,
    SiteType,
    Space,
    SpaceType,
    ZoneType,
)
from plant_health.services import (
    PlantSetupError,
    create_plant_with_location,
)


def _create_household_zone(
    session: Session,
    *,
    household_name: str,
) -> tuple[Household, EnvironmentalZone]:
    """Create a household with one valid plant-placement zone."""

    household = Household(name=household_name)
    session.add(household)
    session.flush()

    site = Site(
        household_id=household.id,
        name=f"{household_name} Site",
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
        name="Plant Shelf",
        zone_type=ZoneType.SHELF,
    )
    session.add(zone)
    session.commit()

    return household, zone


def test_create_plant_with_initial_location() -> None:
    """Creating plants should assign codes and starting locations."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household, zone = _create_household_zone(
            session,
            household_name="Test Household",
        )

        first_result = create_plant_with_location(
            session,
            household_id=household.id,
            zone_id=zone.id,
            nickname="First Orchid",
            acquisition_source="Local nursery",
            placement_label="Left side of shelf",
        )
        second_result = create_plant_with_location(
            session,
            household_id=household.id,
            zone_id=zone.id,
            nickname="Second Orchid",
        )

        assert first_result.plant.plant_code == "PLANT-0001"
        assert second_result.plant.plant_code == "PLANT-0002"
        assert first_result.location.plant_id == first_result.plant.id
        assert first_result.location.zone_id == zone.id
        assert (
            first_result.location.reason
            == LocationChangeReason.INITIAL_PLACEMENT
        )


def test_create_plant_rejects_zone_from_another_household() -> None:
    """A plant cannot be assigned to another household's zone."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        first_household, first_zone = _create_household_zone(
            session,
            household_name="First Household",
        )
        second_household = Household(name="Second Household")
        session.add(second_household)
        session.commit()

        assert first_household.id != second_household.id

        with pytest.raises(
            PlantSetupError,
            match="selected zone does not belong to this household",
        ):
            create_plant_with_location(
                session,
                household_id=second_household.id,
                zone_id=first_zone.id,
                nickname="Incorrectly Assigned Plant",
            )