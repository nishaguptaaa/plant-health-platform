"""Shared FastAPI dependencies, such as database sessions."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from plant_health.database.session import create_database_engine, create_session_factory

_engine = create_database_engine()
_session_factory = create_session_factory(_engine)


def get_db() -> Iterator[Session]:
    """Provide a database session for a single request, then close it."""

    session = _session_factory()
    try:
        yield session
    finally:
        session.close()
