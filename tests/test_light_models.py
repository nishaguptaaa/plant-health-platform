"""Tests for light sources and their zone connections."""

from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import UniqueConstraint

from plant_health.database import Base
from plant_health.database.models import LightSourceType, ZoneLightSource


def test_light_tables_can_be_created() -> None:
    """The light-source tables should be included in the database."""

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    table_names = set(inspect(engine).get_table_names())

    assert "light_sources" in table_names
    assert "zone_light_sources" in table_names


def test_zone_light_source_is_unique_per_pair() -> None:
    """The same light source should not be connected to a zone twice."""

    unique_constraints = [
        constraint
        for constraint in ZoneLightSource.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    unique_column_groups = {
        tuple(column.name for column in constraint.columns)
        for constraint in unique_constraints
    }

    assert ("zone_id", "light_source_id") in unique_column_groups


def test_natural_and_artificial_light_sources_are_supported() -> None:
    """The system should support windows and artificial grow lights."""

    assert LightSourceType.WINDOW.value == "window"
    assert LightSourceType.SKYLIGHT.value == "skylight"
    assert LightSourceType.GROW_LIGHT.value == "grow_light"