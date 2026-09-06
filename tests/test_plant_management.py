"""Tests for editing plant details and identification."""

from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    IdentificationStatus,
    PlantStatus,
    Site,
    SiteType,
    Space,
    SpaceType,
    ZoneType,
)
from plant_health.services import (
    PlantManagementError,
    create_plant_with_location,
    update_plant_details,
)


def _create_test_plant(
    session: Session,
) -> tuple[UUID, UUID]:
    """Create one household, location, and plant for a test."""

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
        nickname="Original Name",
    )

    return household.id, result.plant.id


def test_update_plant_details_and_identification() -> None:
    """Plant details and a confirmed species should be saved."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_test_plant(session)

        result = update_plant_details(
            session,
            household_id=household_id,
            plant_id=plant_id,
            nickname="Leafy",
            status=PlantStatus.DORMANT,
            scientific_name="Epipremnum aureum",
            common_name="Golden Pothos",
            cultivar_name="Marble Queen",
            identification_status=(
                IdentificationStatus.USER_CONFIRMED
            ),
            identification_confidence=Decimal("0.95"),
            acquired_on=date(2025, 1, 15),
            acquisition_source="Local nursery",
            notes="Updated plant details.",
        )

        assert result.plant.nickname == "Leafy"
        assert result.plant.status == PlantStatus.DORMANT
        assert result.plant.cultivar_name == "Marble Queen"
        assert result.plant.identification_status == (
            IdentificationStatus.USER_CONFIRMED
        )
        assert result.plant.identification_confidence == Decimal("0.9500")
        assert result.plant.acquired_on == date(2025, 1, 15)
        assert result.plant.acquisition_source == "Local nursery"
        assert result.plant.notes == "Updated plant details."

        assert result.species is not None
        assert result.plant.species_id == result.species.id
        assert result.species.scientific_name == "Epipremnum aureum"
        assert result.species.primary_common_name == "Golden Pothos"
        assert result.species.human_verified is True


def test_update_plant_rejects_another_household() -> None:
    """A household must not edit a plant belonging to another one."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _, plant_id = _create_test_plant(session)

        other_household = Household(name="Other Household")
        session.add(other_household)
        session.commit()

        with pytest.raises(
            PlantManagementError,
            match="does not belong to this household",
        ):
            update_plant_details(
                session,
                household_id=other_household.id,
                plant_id=plant_id,
                nickname="Unauthorized Rename",
                status=PlantStatus.ACTIVE,
            )


def test_update_plant_requires_scientific_name_for_identification() -> None:
    """Identification details require a scientific species name."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_test_plant(session)

        with pytest.raises(
            PlantManagementError,
            match="Enter a scientific name",
        ):
            update_plant_details(
                session,
                household_id=household_id,
                plant_id=plant_id,
                nickname="Original Name",
                status=PlantStatus.ACTIVE,
                common_name="Pothos",
            )