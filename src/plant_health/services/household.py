"""Services for creating households and their initial owners."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    Household,
    HouseholdMembership,
    HouseholdRole,
    User,
)


class HouseholdSetupError(ValueError):
    """Raised when household setup data is invalid or cannot be saved."""


@dataclass(frozen=True, slots=True)
class HouseholdSetupResult:
    """Records created during initial household setup."""

    user: User
    household: Household
    membership: HouseholdMembership


def _required_text(value: str, *, field_name: str) -> str:
    """Remove surrounding whitespace and reject empty text."""

    cleaned_value = value.strip()

    if not cleaned_value:
        raise HouseholdSetupError(f"{field_name} is required.")

    return cleaned_value


def _normalize_email(email: str) -> str:
    """Normalize and perform a basic validation of an email address."""

    normalized_email = email.strip().lower()

    if (
        not normalized_email
        or "@" not in normalized_email
        or normalized_email.startswith("@")
        or normalized_email.endswith("@")
    ):
        raise HouseholdSetupError("Enter a valid email address.")

    return normalized_email


def create_household_with_owner(
    session: Session,
    *,
    display_name: str,
    email: str,
    household_name: str,
) -> HouseholdSetupResult:
    """Create a household and connect its initial owner."""

    clean_display_name = _required_text(
        display_name,
        field_name="Display name",
    )
    clean_household_name = _required_text(
        household_name,
        field_name="Household name",
    )
    normalized_email = _normalize_email(email)

    try:
        user = session.scalar(
            select(User).where(User.email == normalized_email)
        )

        if user is None:
            user = User(
                email=normalized_email,
                display_name=clean_display_name,
            )
            session.add(user)
            session.flush()

        household = Household(name=clean_household_name)
        session.add(household)
        session.flush()

        membership = HouseholdMembership(
            household_id=household.id,
            user_id=user.id,
            role=HouseholdRole.OWNER,
        )
        session.add(membership)

        session.commit()
        session.refresh(user)
        session.refresh(household)
        session.refresh(membership)
    except IntegrityError as error:
        session.rollback()
        raise HouseholdSetupError(
            "The household could not be created because some information "
            "already exists."
        ) from error
    except Exception:
        session.rollback()
        raise

    return HouseholdSetupResult(
        user=user,
        household=household,
        membership=membership,
    )