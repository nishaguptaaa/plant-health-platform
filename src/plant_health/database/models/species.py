"""Shared biological reference information for plant species."""

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Species(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A biological species shared by multiple individual plants."""

    __tablename__ = "species"
    __table_args__ = (
        UniqueConstraint(
            "scientific_name",
            name="species_scientific_name",
        ),
    )

    scientific_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    primary_common_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    family_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    genus_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_hybrid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    reference_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    reference_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    human_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )