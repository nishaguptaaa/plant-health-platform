"""Tests for loading the saved plant collection."""

from uuid import UUID

from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    Site,
    SiteType,
    Space,
    SpaceType,
    Species,
    ZoneType,
)
from plant_health.services import (
    create_plant_with_location,
    load_plant_collection,
)


def _create_household_plant(
    session: Session,
    *,
    household_name: str,
    plant_name: str,
    scientific_name: str,
) -> tuple[UUID, UUID]:
    """Create the place records and one plant needed by a test."""

    household = Household(name=household_name)
    session.add(household)
    session.flush()

    site = Site(
        household_id=household.id,
        name=f"{household_name} Home",
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

    species = Species(
        scientific_name=scientific_name,
        primary_common_name="Golden Pothos",
        human_verified=True,
    )
    session.add(species)
    session.commit()

    result = create_plant_with_location(
        session,
        household_id=household.id,
        zone_id=zone.id,
        nickname=plant_name,
        species_id=species.id,
    )

    return household.id, result.plant.id


def test_load_plant_collection_includes_current_location() -> None:
    """A plant should include its household, species, and current place."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_household_plant(
            session,
            household_name="Test Household",
            plant_name="Leafy",
            scientific_name="Epipremnum aureum",
        )

        collection = load_plant_collection(
            session,
            household_ids=[household_id],
        )

        assert len(collection) == 1

        plant = collection[0]

        assert plant.id == plant_id
        assert plant.household_id == household_id
        assert plant.household_name == "Test Household"
        assert plant.nickname == "Leafy"
        assert plant.scientific_name == "Epipremnum aureum"
        assert plant.common_name == "Golden Pothos"
        assert plant.site_name == "Test Household Home"
        assert plant.space_name == "Living Room"
        assert plant.zone_name == "Window Shelf"


def test_load_plant_collection_respects_household_filter() -> None:
    """A household filter should hide plants from other households."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        first_household_id, first_plant_id = _create_household_plant(
            session,
            household_name="First Household",
            plant_name="First Plant",
            scientific_name="Monstera deliciosa",
        )
        _create_household_plant(
            session,
            household_name="Second Household",
            plant_name="Second Plant",
            scientific_name="Dracaena trifasciata",
        )

        collection = load_plant_collection(
            session,
            household_ids=[first_household_id],
        )

        assert len(collection) == 1
        assert collection[0].id == first_plant_id
        assert collection[0].household_name == "First Household"

        assert load_plant_collection(
            session,
            household_ids=[],
        ) == []