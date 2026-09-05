"""Tests for the Places hierarchy service."""

from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    Site,
    SiteType,
    Space,
    SpaceType,
    ZoneType,
)
from plant_health.services import load_place_hierarchy


def test_load_place_hierarchy() -> None:
    """Sites, spaces, and zones should be grouped under their household."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
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
            name="Bookshelf Top Shelf",
            zone_type=ZoneType.SHELF,
        )
        session.add(zone)
        session.commit()

        hierarchy = load_place_hierarchy(
            session,
            household_ids=[household.id],
        )

        assert len(hierarchy) == 1
        assert hierarchy[0].name == "Test Household"
        assert hierarchy[0].sites[0].name == "Test Home"
        assert hierarchy[0].sites[0].spaces[0].name == "Living Room"
        assert (
            hierarchy[0]
            .sites[0]
            .spaces[0]
            .zones[0]
            .name
            == "Bookshelf Top Shelf"
        )


def test_load_place_hierarchy_with_no_authorized_households() -> None:
    """No places should load when the user has no household access."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")

    with Session(engine) as session:
        hierarchy = load_place_hierarchy(
            session,
            household_ids=[],
        )

    assert hierarchy == []