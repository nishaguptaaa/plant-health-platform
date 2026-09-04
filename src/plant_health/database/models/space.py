"""Spaces within a site, including rooms and nested growing areas."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from plant_health.database.models.site import Site


class SpaceType(StrEnum):
    """Kinds of spaces that can contain plants or smaller spaces."""

    ROOM = "room"
    BASEMENT = "basement"
    SUNROOM = "sunroom"
    GREENHOUSE = "greenhouse"
    BALCONY = "balcony"
    PATIO = "patio"
    PORCH = "porch"
    GROW_TENT = "grow_tent"
    SHELF = "shelf"
    OUTDOOR_BED = "outdoor_bed"
    OTHER = "other"


class Space(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A room or growing area within a site."""

    __tablename__ = "spaces"
    __table_args__ = (
        CheckConstraint(
            "height_above_ground_m IS NULL "
            "OR height_above_ground_m BETWEEN -20 AND 1000",
            name="valid_height_above_ground",
        ),
        CheckConstraint(
            "below_grade_fraction_pct IS NULL "
            "OR below_grade_fraction_pct BETWEEN 0 AND 100",
            name="valid_below_grade_fraction",
        ),
    )

    site_id: Mapped[UUID] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_space_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("spaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    space_type: Mapped[SpaceType] = mapped_column(
        Enum(
            SpaceType,
            name="space_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    floor_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_above_ground_m: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )
    below_grade_fraction_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    site: Mapped[Site] = relationship()
    parent: Mapped[Space | None] = relationship(
        back_populates="children",
        remote_side=lambda: [Space.id],
    )
    children: Mapped[list[Space]] = relationship(back_populates="parent")