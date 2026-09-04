"""Individual plant records."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
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
)

if TYPE_CHECKING:
    from plant_health.database.models.identity import Household
    from plant_health.database.models.species import Species


class PlantStatus(StrEnum):
    """Current lifecycle status of an individual plant."""

    ACTIVE = "active"
    DORMANT = "dormant"
    QUARANTINED = "quarantined"
    DECEASED = "deceased"
    TRANSFERRED = "transferred"
    UNKNOWN = "unknown"


class IdentificationStatus(StrEnum):
    """How the plant's species identification was established."""

    UNCONFIRMED = "unconfirmed"
    AI_SUGGESTED = "ai_suggested"
    USER_CONFIRMED = "user_confirmed"
    EXPERT_CONFIRMED = "expert_confirmed"


class Plant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One biological plant with its own identity and history."""

    __tablename__ = "plants"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "plant_code",
            name="plant_code_per_household",
        ),
        CheckConstraint(
            "identification_confidence IS NULL "
            "OR (identification_confidence >= 0 "
            "AND identification_confidence <= 1)",
            name="plant_identification_confidence_range",
        ),
        CheckConstraint(
            "deceased_on IS NULL "
            "OR acquired_on IS NULL "
            "OR deceased_on >= acquired_on",
            name="plant_deceased_after_acquired",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    species_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("species.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_plant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    plant_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    nickname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    cultivar_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    status: Mapped[PlantStatus] = mapped_column(
        Enum(
            PlantStatus,
            name="plant_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=PlantStatus.ACTIVE,
        nullable=False,
    )
    identification_status: Mapped[IdentificationStatus] = mapped_column(
        Enum(
            IdentificationStatus,
            name="plant_identification_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=IdentificationStatus.UNCONFIRMED,
        nullable=False,
    )
    identification_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    acquired_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    acquisition_source: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    deceased_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    household: Mapped[Household] = relationship()
    species: Mapped[Species | None] = relationship()
    parent_plant: Mapped[Plant | None] = relationship(
        remote_side="Plant.id",
        back_populates="propagated_plants",
    )
    propagated_plants: Mapped[list[Plant]] = relationship(
        back_populates="parent_plant",
    )