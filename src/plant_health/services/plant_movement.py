"""Services for moving plants while preserving location history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    EnvironmentalZone,
    LocationChangeReason,
    Plant,
    PlantLocationHistory,
    Site,
    Space,
)
from plant_health.database.models.common import utc_now


class PlantMovementError(ValueError):
    """Raised when a plant cannot be moved to a selected zone."""


@dataclass(frozen=True, slots=True)
class PlantMovementResult:
    """The plant, closed location, and new current location."""

    plant: Plant
    previous_location: PlantLocationHistory | None
    new_location: PlantLocationHistory


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values."""

    if value is None:
        return None

    cleaned_value = value.strip()
    return cleaned_value or None


def _as_utc(value: datetime) -> datetime:
    """Return a timezone-aware UTC value for safe comparisons."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def move_plant(
    session: Session,
    *,
    household_id: UUID,
    plant_id: UUID,
    new_zone_id: UUID,
    reason: LocationChangeReason,
    moved_at: datetime | None = None,
    placement_label: str | None = None,
    notes: str | None = None,
) -> PlantMovementResult:
    """Close the current placement and create a new current placement."""

    plant = session.get(Plant, plant_id)

    if plant is None or plant.household_id != household_id:
        raise PlantMovementError(
            "The selected plant does not belong to this household."
        )

    new_zone = session.get(EnvironmentalZone, new_zone_id)

    if new_zone is None or not new_zone.active:
        raise PlantMovementError(
            "The selected destination zone is not available."
        )

    new_space = session.get(Space, new_zone.space_id)

    if new_space is None or not new_space.active:
        raise PlantMovementError(
            "The destination zone does not belong to an active space."
        )

    new_site = session.get(Site, new_space.site_id)

    if (
        new_site is None
        or not new_site.active
        or new_site.household_id != household_id
    ):
        raise PlantMovementError(
            "The destination zone does not belong to this household."
        )

    if reason == LocationChangeReason.INITIAL_PLACEMENT:
        raise PlantMovementError(
            "Initial placement cannot be used as a movement reason."
        )

    current_locations = list(
        session.scalars(
            select(PlantLocationHistory)
            .where(
                PlantLocationHistory.plant_id == plant_id,
                PlantLocationHistory.ended_at.is_(None),
            )
            .order_by(PlantLocationHistory.started_at.desc())
        ).all()
    )

    if len(current_locations) > 1:
        raise PlantMovementError(
            "This plant has multiple current locations and must be "
            "corrected before it can be moved."
        )

    previous_location = (
        current_locations[0] if current_locations else None
    )

    if (
        previous_location is not None
        and previous_location.zone_id == new_zone_id
    ):
        raise PlantMovementError(
            "The plant is already in the selected zone."
        )

    movement_time = moved_at or utc_now()

    if _as_utc(movement_time) > _as_utc(utc_now()):
        raise PlantMovementError(
            "The movement time cannot be in the future."
        )

    if (
        previous_location is not None
        and _as_utc(movement_time)
        <= _as_utc(previous_location.started_at)
    ):
        raise PlantMovementError(
            "The movement time must be after the current placement began."
        )

    clean_placement_label = _optional_text(placement_label)
    clean_notes = _optional_text(notes)

    new_location = PlantLocationHistory(
        plant_id=plant.id,
        zone_id=new_zone.id,
        started_at=movement_time,
        reason=reason,
        placement_label=clean_placement_label,
        notes=clean_notes,
    )

    try:
        if previous_location is not None:
            previous_location.ended_at = movement_time

        session.add(new_location)
        session.commit()

        session.refresh(plant)
        session.refresh(new_location)

        if previous_location is not None:
            session.refresh(previous_location)
    except IntegrityError as error:
        session.rollback()
        raise PlantMovementError(
            "The plant movement could not be saved."
        ) from error
    except Exception:
        session.rollback()
        raise

    return PlantMovementResult(
        plant=plant,
        previous_location=previous_location,
        new_location=new_location,
    )