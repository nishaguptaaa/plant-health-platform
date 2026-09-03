"""Tests for the shared SQLAlchemy database foundation."""

from plant_health.database import Base


def test_base_uses_constraint_naming_convention() -> None:
    """Every database constraint type should have a naming rule."""

    expected_keys = {"ix", "uq", "ck", "fk", "pk"}

    assert set(Base.metadata.naming_convention) == expected_keys