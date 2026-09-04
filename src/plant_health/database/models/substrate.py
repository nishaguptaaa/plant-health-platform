"""Substrate components, mixtures, and plant substrate history."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utc_now,
)

if TYPE_CHECKING:
    from plant_health.database.models.identity import Household
    from plant_health.database.models.plant import Plant


class SubstrateCategory(StrEnum):
    """Broad categories of substrate ingredients."""

    ORGANIC = "organic"
    MINERAL = "mineral"
    INERT = "inert"
    LIVING = "living"
    SYNTHETIC = "synthetic"
    OTHER = "other"


class SubstrateComponent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A reusable ingredient that may appear in substrate mixtures."""

    __tablename__ = "substrate_components"
    __table_args__ = (
        UniqueConstraint(
            "name",
            name="substrate_component_name",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    category: Mapped[SubstrateCategory] = mapped_column(
        Enum(
            SubstrateCategory,
            name="substrate_category",
            native_enum=False,
            validate_strings=True,
        ),
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


class SubstrateMix(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A named reusable substrate recipe owned by a household."""

    __tablename__ = "substrate_mixes"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "mix_code",
            name="substrate_mix_code_per_household",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mix_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    household: Mapped[Household] = relationship()


class SubstrateMixComponent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One ingredient and its relative amount in a substrate mixture."""

    __tablename__ = "substrate_mix_components"
    __table_args__ = (
        UniqueConstraint(
            "mix_id",
            "component_id",
            name="substrate_component_per_mix",
        ),
        CheckConstraint(
            "proportion_parts > 0",
            name="substrate_component_parts_positive",
        ),
    )

    mix_id: Mapped[UUID] = mapped_column(
        ForeignKey("substrate_mixes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_id: Mapped[UUID] = mapped_column(
        ForeignKey("substrate_components.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proportion_parts: Mapped[Decimal] = mapped_column(
        Numeric(8, 3),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    mix: Mapped[SubstrateMix] = relationship()
    component: Mapped[SubstrateComponent] = relationship()


class PlantSubstrateHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A period when an individual plant used a substrate mixture."""

    __tablename__ = "plant_substrate_history"
    __table_args__ = (
        UniqueConstraint(
            "plant_id",
            "started_at",
            name="plant_substrate_start_per_plant",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="plant_substrate_end_after_start",
        ),
    )

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mix_id: Mapped[UUID] = mapped_column(
        ForeignKey("substrate_mixes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    plant: Mapped[Plant] = relationship()
    mix: Mapped[SubstrateMix] = relationship()