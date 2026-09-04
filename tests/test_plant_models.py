"""Tests for species and individual plant records."""

from datetime import date

from plant_health.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from plant_health.database.models import (
    Household,
    IdentificationStatus,
    Plant,
    PlantStatus,
    Species,
)


def test_multiple_plants_can_share_one_species() -> None:
    """Individual plants may share biological reference information."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Test Household")
        species = Species(
            scientific_name="Monstera deliciosa",
            primary_common_name="Swiss cheese plant",
            human_verified=True,
        )
        first_plant = Plant(
            household=household,
            species=species,
            plant_code="P001",
            nickname="Large Monstera",
            status=PlantStatus.ACTIVE,
            identification_status=IdentificationStatus.USER_CONFIRMED,
            acquired_on=date(2026, 1, 10),
        )
        second_plant = Plant(
            household=household,
            species=species,
            plant_code="P002",
            nickname="Small Monstera",
            status=PlantStatus.ACTIVE,
            identification_status=IdentificationStatus.USER_CONFIRMED,
            acquired_on=date(2026, 4, 15),
        )

        session.add_all([first_plant, second_plant])
        session.commit()

        assert first_plant.species_id == species.id
        assert second_plant.species_id == species.id
        assert first_plant.id != second_plant.id


def test_propagated_plant_can_reference_parent() -> None:
    """A propagated plant should retain a connection to its parent plant."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Propagation Household")
        species = Species(scientific_name="Epipremnum aureum")
        parent = Plant(
            household=household,
            species=species,
            plant_code="P001",
            nickname="Parent Pothos",
        )
        cutting = Plant(
            household=household,
            species=species,
            plant_code="P002",
            nickname="Pothos Cutting",
            parent_plant=parent,
        )

        session.add_all([parent, cutting])
        session.commit()

        assert cutting.parent_plant_id == parent.id
        assert cutting in parent.propagated_plants