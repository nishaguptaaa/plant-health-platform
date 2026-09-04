"""Tests for substrate components, mixtures, and plant history."""

from datetime import UTC, datetime
from decimal import Decimal

from plant_health.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from plant_health.database.models import (
    Household,
    Plant,
    PlantSubstrateHistory,
    SubstrateCategory,
    SubstrateComponent,
    SubstrateMix,
    SubstrateMixComponent,
)


def test_substrate_mix_supports_ratio_parts() -> None:
    """A mixture should support two parts bark to one part perlite."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Test Household")
        bark = SubstrateComponent(
            name="Orchid Bark",
            category=SubstrateCategory.ORGANIC,
        )
        perlite = SubstrateComponent(
            name="Perlite",
            category=SubstrateCategory.MINERAL,
        )
        mix = SubstrateMix(
            household=household,
            mix_code="M001",
            name="Aroid Mix",
        )
        bark_portion = SubstrateMixComponent(
            mix=mix,
            component=bark,
            proportion_parts=Decimal(2),
        )
        perlite_portion = SubstrateMixComponent(
            mix=mix,
            component=perlite,
            proportion_parts=Decimal(1),
        )

        session.add_all([bark_portion, perlite_portion])
        session.commit()

        assert bark_portion.proportion_parts == Decimal(2)
        assert perlite_portion.proportion_parts == Decimal(1)
        assert bark_portion.mix_id == perlite_portion.mix_id


def test_plant_can_retain_substrate_history() -> None:
    """A plant should retain the mixture and date of a substrate change."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        household = Household(name="Substrate Household")
        plant = Plant(
            household=household,
            plant_code="P001",
            nickname="Test Plant",
        )
        mix = SubstrateMix(
            household=household,
            mix_code="M001",
            name="Houseplant Mix",
        )
        substrate_history = PlantSubstrateHistory(
            plant=plant,
            mix=mix,
            started_at=datetime(2026, 9, 4, tzinfo=UTC),
            notes="Repotted into a fresh mixture.",
        )

        session.add(substrate_history)
        session.commit()

        assert substrate_history.plant_id == plant.id
        assert substrate_history.mix_id == mix.id
        assert substrate_history.ended_at is None