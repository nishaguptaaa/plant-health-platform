"""Services for creating environmental zones within spaces."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    EnvironmentalZone,
    ObstructionLevel,
    Space,
    ZoneType,
)


class ZoneSetupError(ValueError):
    """Raised when environmental-zone information is invalid."""


def _required_text(value: str, *, field_name: str) -> str:
    """Remove surrounding whitespace and reject empty text."""

    cleaned_value = value.strip()

    if not cleaned_value:
        raise ZoneSetupError(f"{field_name} is required.")

    return cleaned_value


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values."""

    if value is None:
        return None

    cleaned_value = value.strip()
    return cleaned_value or None


def create_environmental_zone(
    session: Session,
    *,
    space_id: UUID,
    name: str,
    zone_type: ZoneType,
    description: str | None = None,
    height_above_floor_m: Decimal | None = None,
    direct_sun_possible: bool | None = None,
    obstruction_level: ObstructionLevel = ObstructionLevel.UNKNOWN,
    estimated_sky_view_pct: Decimal | None = None,
) -> EnvironmentalZone:
    """Create and save a plant-placement microenvironment."""

    clean_name = _required_text(name, field_name="Zone name")
    clean_description = _optional_text(description)

    if (
        height_above_floor_m is not None
        and height_above_floor_m < Decimal(0)
    ):
        raise ZoneSetupError(
            "Height above the floor cannot be negative."
        )

    if estimated_sky_view_pct is not None and not (
        Decimal(0)
        <= estimated_sky_view_pct
        <= Decimal(100)
    ):
        raise ZoneSetupError(
            "Estimated sky-view percentage must be between 0 and 100."
        )

    space = session.get(Space, space_id)

    if space is None:
        raise ZoneSetupError("The selected space does not exist.")

    existing_zone = session.scalar(
        select(EnvironmentalZone).where(
            EnvironmentalZone.space_id == space_id,
            EnvironmentalZone.name == clean_name,
        )
    )

    if existing_zone is not None:
        raise ZoneSetupError(
            "A zone with this name already exists in the selected space."
        )

    zone = EnvironmentalZone(
        space_id=space_id,
        name=clean_name,
        zone_type=zone_type,
        description=clean_description,
        height_above_floor_m=height_above_floor_m,
        direct_sun_possible=direct_sun_possible,
        obstruction_level=obstruction_level,
        estimated_sky_view_pct=estimated_sky_view_pct,
        active=True,
    )

    try:
        session.add(zone)
        session.commit()
        session.refresh(zone)
    except IntegrityError as error:
        session.rollback()
        raise ZoneSetupError(
            "The environmental zone could not be saved."
        ) from error
    except Exception:
        session.rollback()
        raise

    return zone