"""Tests for the space setup service."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    Household,
    Site,
    SiteType,
    SpaceType,
)
from plant_health.services import SpaceSetupError, create_space


def test_create_space() -> None:
    """A valid space should be saved under its site."""

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
        session.commit()

        space = create_space(
            session,
            site_id=site.id,
            name="Living Room",
            space_type=SpaceType.ROOM,
            floor_number=1,
            height_above_ground_m=Decimal("3.00"),
            below_grade_fraction_pct=Decimal(0),
            notes="Main room with several windows.",
        )

        assert space.name == "Living Room"
        assert space.site_id == site.id
        assert space.space_type == SpaceType.ROOM
        assert space.floor_number == 1


def test_create_space_rejects_invalid_below_grade_percentage() -> None:
    """Below-grade percentages cannot exceed 100."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")

    with Session(engine) as session, pytest.raises(
        SpaceSetupError,
        match="Below-grade percentage must be between 0 and 100",
    ):
        create_space(
            session,
            site_id=Household().id,
            name="Basement",
            space_type=SpaceType.BASEMENT,
            below_grade_fraction_pct=Decimal(101),
        )