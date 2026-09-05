"""Services for creating spaces within sites."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import Site, Space, SpaceType


class SpaceSetupError(ValueError):
    """Raised when space setup information is invalid."""


def _required_text(value: str, *, field_name: str) -> str:
    """Remove surrounding whitespace and reject empty text."""

    cleaned_value = value.strip()

    if not cleaned_value:
        raise SpaceSetupError(f"{field_name} is required.")

    return cleaned_value


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values."""

    if value is None:
        return None

    cleaned_value = value.strip()
    return cleaned_value or None


def create_space(
    session: Session,
    *,
    site_id: UUID,
    name: str,
    space_type: SpaceType,
    parent_space_id: UUID | None = None,
    floor_number: int | None = None,
    height_above_ground_m: Decimal | None = None,
    below_grade_fraction_pct: Decimal | None = None,
    notes: str | None = None,
) -> Space:
    """Create and save a room or growing area within a site."""

    clean_name = _required_text(name, field_name="Space name")
    clean_notes = _optional_text(notes)

    if height_above_ground_m is not None and not (
        Decimal(-20)
        <= height_above_ground_m
        <= Decimal(1000)
    ):
        raise SpaceSetupError(
            "Height above ground must be between -20 and 1000 meters."
        )

    if below_grade_fraction_pct is not None and not (
        Decimal(0)
        <= below_grade_fraction_pct
        <= Decimal(100)
    ):
        raise SpaceSetupError(
            "Below-grade percentage must be between 0 and 100."
        )

    site = session.get(Site, site_id)

    if site is None:
        raise SpaceSetupError("The selected site does not exist.")

    if parent_space_id is not None:
        parent_space = session.get(Space, parent_space_id)

        if parent_space is None:
            raise SpaceSetupError("The selected parent space does not exist.")

        if parent_space.site_id != site_id:
            raise SpaceSetupError(
                "A parent space must belong to the same site."
            )

    existing_space = session.scalar(
        select(Space).where(
            Space.site_id == site_id,
            Space.parent_space_id == parent_space_id,
            Space.name == clean_name,
        )
    )

    if existing_space is not None:
        raise SpaceSetupError(
            "A space with this name already exists at this level."
        )

    space = Space(
        site_id=site_id,
        parent_space_id=parent_space_id,
        name=clean_name,
        space_type=space_type,
        floor_number=floor_number,
        height_above_ground_m=height_above_ground_m,
        below_grade_fraction_pct=below_grade_fraction_pct,
        notes=clean_notes,
        active=True,
    )

    try:
        session.add(space)
        session.commit()
        session.refresh(space)
    except IntegrityError as error:
        session.rollback()
        raise SpaceSetupError("The space could not be saved.") from error
    except Exception:
        session.rollback()
        raise

    return space