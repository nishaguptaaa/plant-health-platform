"""Tests for database engine and session configuration."""

from sqlalchemy import text

from plant_health.database import (
    create_database_engine,
    create_session_factory,
)


def test_sqlite_foreign_keys_are_enabled() -> None:
    """SQLite should enforce relationships between tables."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")

    with engine.connect() as connection:
        foreign_keys_enabled = connection.execute(
            text("PRAGMA foreign_keys")
        ).scalar_one()

    engine.dispose()

    assert foreign_keys_enabled == 1


def test_session_factory_uses_supplied_engine() -> None:
    """Created sessions should connect through the supplied engine."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        assert session.get_bind() is engine

    engine.dispose()