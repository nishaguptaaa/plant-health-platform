"""Containers and individual plant container history."""

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


class ContainerType(StrEnum):
    """Physical forms a plant container may take."""

    NURSERY_POT = "nursery_pot"
    STANDARD_POT = "standard_pot"
    CACHEPOT = "cachepot"
    HANGING_BASKET = "hanging_basket"
    SELF_WATERING_POT = "self_watering_pot"
    VASE = "vase"
    JAR = "jar"
    RESERVOIR = "reservoir"
    NET_POT = "net_pot"
    MOUNT = "mount"
    OTHER = "other"


class ContainerMaterial(StrEnum):
    """Materials from which containers may be made."""

    PLASTIC = "plastic"
    TERRACOTTA = "terracotta"
    CERAMIC = "ceramic"
    GLASS = "glass"
    METAL = "metal"
    WOOD = "wood"
    FABRIC = "fabric"
    CONCRETE = "concrete"
    OTHER = "other"
    UNKNOWN = "unknown"


class PlantContainerRole(StrEnum):
    """The role a container serves for a particular plant."""

    ROOT_CONTAINER = "root_container"
    OUTER_CACHEPOT = "outer_cachepot"
    RESERVOIR = "reservoir"
    MOUNT = "mount"
    SUPPORT = "support"
    OTHER = "other"


class Container(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A reusable physical container owned by a household."""

    __tablename__ = "containers"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "container_code",
            name="container_code_per_household",
        ),
        CheckConstraint(
            "diameter_cm IS NULL OR diameter_cm > 0",
            name="container_diameter_positive",
        ),
        CheckConstraint(
            "width_cm IS NULL OR width_cm > 0",
            name="container_width_positive",
        ),
        CheckConstraint(
            "depth_cm IS NULL OR depth_cm > 0",
            name="container_depth_positive",
        ),
        CheckConstraint(
            "height_cm IS NULL OR height_cm > 0",
            name="container_height_positive",
        ),
        CheckConstraint(
            "volume_l IS NULL OR volume_l > 0",
            name="container_volume_positive",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    container_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )
    container_type: Mapped[ContainerType] = mapped_column(
        Enum(
            ContainerType,
            name="container_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    material: Mapped[ContainerMaterial] = mapped_column(
        Enum(
            ContainerMaterial,
            name="container_material",
            native_enum=False,
            validate_strings=True,
        ),
        default=ContainerMaterial.UNKNOWN,
        nullable=False,
    )

    diameter_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    width_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    depth_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    height_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    volume_l: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 3),
        nullable=True,
    )

    has_drainage: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    is_self_watering: Mapped[bool | None] = mapped_column(
        Boolean,
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


class PlantContainerHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A period when a container served a particular plant."""

    __tablename__ = "plant_container_history"
    __table_args__ = (
        UniqueConstraint(
            "plant_id",
            "container_id",
            "started_at",
            name="plant_container_start",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="plant_container_end_after_start",
        ),
    )

    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    container_id: Mapped[UUID] = mapped_column(
        ForeignKey("containers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    role: Mapped[PlantContainerRole] = mapped_column(
        Enum(
            PlantContainerRole,
            name="plant_container_role",
            native_enum=False,
            validate_strings=True,
        ),
        default=PlantContainerRole.ROOT_CONTAINER,
        nullable=False,
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
    container: Mapped[Container] = relationship()