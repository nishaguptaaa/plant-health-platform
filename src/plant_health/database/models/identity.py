"""User, household, and household-membership models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utc_now,
)


class HouseholdRole(StrEnum):
    """Permission levels available within a household."""

    OWNER = "owner"
    ADMIN = "admin"
    CARETAKER = "caretaker"
    MEMBER = "member"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A person who can access one or more households."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    memberships: Mapped[list[HouseholdMembership]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )


class Household(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A private data boundary shared by related users."""

    __tablename__ = "households"

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    memberships: Mapped[list[HouseholdMembership]] = relationship(
        back_populates="household",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class HouseholdMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user's role and membership history within a household."""

    __tablename__ = "household_memberships"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "user_id",
            name="household_membership_once",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[HouseholdRole] = mapped_column(
        Enum(
            HouseholdRole,
            name="household_role",
            native_enum=False,
            validate_strings=True,
        ),
        default=HouseholdRole.MEMBER,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    household: Mapped[Household] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")