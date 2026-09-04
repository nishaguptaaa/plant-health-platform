"""Tests for containers and plant growing methods."""

from datetime import UTC, datetime
from decimal import Decimal

from plant_health.database import Base, create_database_engine, create_session_factory
from plant_health.database.models import (
    Container,
    ContainerMaterial,
    ContainerType,
    GrowingMethodType,
    Household,
    Plant,
    PlantContainerHistory,
    PlantContainerRole,
    PlantCultivationHistory,
)


def test_plant_can_be_connected_to_a_draining_pot() -> None:
    """A plant should retain a dated connection to its physical container."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Test Household")
        plant = Plant(
            household=household,
            plant_code="P001",
            nickname="Test Plant",
        )
        pot = Container(
            household=household,
            container_code="C001",
            name="Six-inch Nursery Pot",
            container_type=ContainerType.NURSERY_POT,
            material=ContainerMaterial.PLASTIC,
            diameter_cm=Decimal("15.24"),
            has_drainage=True,
        )
        container_history = PlantContainerHistory(
            plant=plant,
            container=pot,
            role=PlantContainerRole.ROOT_CONTAINER,
            started_at=datetime(2026, 9, 1, tzinfo=UTC),
        )

        session.add(container_history)
        session.commit()

        assert container_history.plant_id == plant.id
        assert container_history.container_id == pot.id
        assert pot.has_drainage is True


def test_vase_and_water_culture_are_stored_separately() -> None:
    """The physical container and growing method are separate concepts."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Water Culture Household")
        plant = Plant(
            household=household,
            plant_code="P001",
            nickname="Water-Grown Pothos",
        )
        vase = Container(
            household=household,
            container_code="C001",
            name="Glass Vase",
            container_type=ContainerType.VASE,
            material=ContainerMaterial.GLASS,
            has_drainage=False,
        )
        container_history = PlantContainerHistory(
            plant=plant,
            container=vase,
            role=PlantContainerRole.RESERVOIR,
            started_at=datetime(2026, 9, 1, tzinfo=UTC),
        )
        cultivation_history = PlantCultivationHistory(
            plant=plant,
            method_type=GrowingMethodType.FULL_WATER_CULTURE,
            started_at=datetime(2026, 9, 1, tzinfo=UTC),
            root_submersion_percent=Decimal("30.0"),
        )

        session.add_all([container_history, cultivation_history])
        session.commit()

        assert vase.container_type == ContainerType.VASE
        assert (
            cultivation_history.method_type
            == GrowingMethodType.FULL_WATER_CULTURE
        )
        assert cultivation_history.root_submersion_percent == Decimal("30.0")