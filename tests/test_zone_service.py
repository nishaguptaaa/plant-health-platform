"""Tests for the environmental-zone setup service."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    Household,
    ObstructionLevel,
    Site,
    SiteType,
    Space,
    SpaceType,
    ZoneType,
)
from plant_health.services import (
    ZoneSetupError,
    create_environmental_zone,
)


def test_create_environmental_zone() -> None:
    """A valid environmental zone should be saved under its space."""

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
        session.commit()

        zone = create_environmental_zone(
            session,
            space_id=space.id,
            name="South Windowsill",
            zone_type=ZoneType.WINDOWSILL,
            description="Windowsill beside the main living-room window.",
            height_above_floor_m=Decimal("0.90"),
            direct_sun_possible=True,
            obstruction_level=ObstructionLevel.LOW,
            estimated_sky_view_pct=Decimal(80),
        )

        assert zone.name == "South Windowsill"
        assert zone.space_id == space.id
        assert zone.zone_type == ZoneType.WINDOWSILL
        assert zone.height_above_floor_m == Decimal("0.90")
        assert zone.direct_sun_possible is True


def test_create_environmental_zone_rejects_invalid_sky_view() -> None:
    """The estimated sky-view percentage cannot exceed 100."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")

    with Session(engine) as session, pytest.raises(
        ZoneSetupError,
        match="Estimated sky-view percentage must be between 0 and 100",
    ):
        create_environmental_zone(
            session,
            space_id=uuid4(),
            name="Invalid Zone",
            zone_type=ZoneType.WINDOWSILL,
            estimated_sky_view_pct=Decimal(101),
        )