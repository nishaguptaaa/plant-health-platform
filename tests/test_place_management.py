"""Tests for renaming and deactivating saved places."""

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
from plant_health.services import (
    deactivate_site,
    deactivate_space,
    deactivate_zone,
    rename_household,
    rename_site,
    rename_space,
    rename_zone,
)


def create_test_places(
    session: Session,
) -> tuple[Household, Site, Space, EnvironmentalZone]:
    """Create a complete place hierarchy for a test."""

    household = Household(name="Original Household")
    session.add(household)
    session.flush()

    site = Site(
        household_id=household.id,
        name="Original Site",
        site_type=SiteType.HOUSE,
        timezone="America/New_York",
        weather_enabled=False,
    )
    session.add(site)
    session.flush()

    space = Space(
        site_id=site.id,
        name="Original Room",
        space_type=SpaceType.ROOM,
    )
    session.add(space)
    session.flush()

    zone = EnvironmentalZone(
        space_id=space.id,
        name="Original Shelf",
        zone_type=ZoneType.SHELF,
    )
    session.add(zone)
    session.commit()

    return household, site, space, zone


def test_rename_saved_places() -> None:
    """Renaming should preserve each record and its relationships."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household, site, space, zone = create_test_places(session)

        renamed_household = rename_household(
            session,
            household_id=household.id,
            new_name="Family Household",
        )
        renamed_site = rename_site(
            session,
            site_id=site.id,
            new_name="Family Home",
        )
        renamed_space = rename_space(
            session,
            space_id=space.id,
            new_name="Main Living Room",
        )
        renamed_zone = rename_zone(
            session,
            zone_id=zone.id,
            new_name="Bookshelf Top Shelf",
        )

        assert renamed_household.name == "Family Household"
        assert renamed_site.name == "Family Home"
        assert renamed_space.name == "Main Living Room"
        assert renamed_zone.name == "Bookshelf Top Shelf"
        assert renamed_space.site_id == renamed_site.id
        assert renamed_zone.space_id == renamed_space.id


def test_deactivate_saved_places() -> None:
    """Deactivation should hide records without deleting them."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _, site, space, zone = create_test_places(session)

        deactivated_zone = deactivate_zone(
            session,
            zone_id=zone.id,
        )
        deactivated_space = deactivate_space(
            session,
            space_id=space.id,
        )
        deactivated_site = deactivate_site(
            session,
            site_id=site.id,
        )

        assert deactivated_zone.active is False
        assert deactivated_space.active is False
        assert deactivated_site.active is False

        assert session.get(EnvironmentalZone, zone.id) is not None
        assert session.get(Space, space.id) is not None
        assert session.get(Site, site.id) is not None