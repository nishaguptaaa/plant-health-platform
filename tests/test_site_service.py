"""Tests for site setup services."""

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from plant_health.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from plant_health.database.models import (
    Household,
    Site,
    SiteType,
    TerrainPosition,
)
from plant_health.services import SiteSetupError, create_site


def test_create_site_saves_geographic_context() -> None:
    """A site should retain its household and environmental context."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Test Household")
        session.add(household)
        session.commit()
        session.refresh(household)

        site = create_site(
            session,
            household_id=household.id,
            name="Test Home",
            site_type=SiteType.HOUSE,
            timezone="America/New_York",
            address_text="Test City",
            latitude=Decimal("42.300000"),
            longitude=Decimal("-71.700000"),
            elevation_m=Decimal("120.50"),
            terrain_position=TerrainPosition.SLOPE,
            terrain_slope_degrees=Decimal("8.50"),
            weather_enabled=True,
            weather_sync_interval_minutes=60,
        )

        assert site.household_id == household.id
        assert site.name == "Test Home"
        assert site.site_type == SiteType.HOUSE
        assert site.timezone == "America/New_York"
        assert site.terrain_position == TerrainPosition.SLOPE
        assert site.weather_enabled is True
        assert session.scalar(select(func.count(Site.id))) == 1

    engine.dispose()


def test_create_site_requires_coordinates_for_weather() -> None:
    """Weather tracking should not be enabled without coordinates."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        with pytest.raises(
            SiteSetupError,
            match="Weather tracking requires latitude and longitude",
        ):
            create_site(
                session,
                household_id=Household().id,
                name="Site Without Coordinates",
                site_type=SiteType.APARTMENT,
                timezone="America/New_York",
                weather_enabled=True,
            )

        assert session.scalar(select(func.count(Site.id))) == 0

    engine.dispose()