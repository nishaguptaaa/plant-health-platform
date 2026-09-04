"""Tests for fields shared by database models."""

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from plant_health.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from plant_health.database.models import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class ExampleRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Small model used only to test the shared fields."""

    __tablename__ = "test_example_records"

    name: Mapped[str] = mapped_column(String(50), nullable=False)


def test_common_fields_are_generated() -> None:
    """Saving a record should generate its UUID and timestamps."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine)
    Base.metadata.create_all(engine)

    record = ExampleRecord(name="Example")

    with session_factory() as session:
        session.add(record)
        session.commit()

    assert isinstance(record.id, UUID)
    assert record.created_at.tzinfo is not None
    assert record.updated_at.tzinfo is not None

    Base.metadata.drop_all(engine)
    engine.dispose()