"""Services for adding individual plants to a household."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    IdentificationStatus,
    LocationChangeReason,
    Plant,
    PlantLocationHistory,
    PlantStatus,
    Site,
    Space,
    Species,
)
from plant_health.database.models.common import utc_now


class PlantSetupError(ValueError):
    """Raised when a plant cannot be created."""


@dataclass(frozen=True, slots=True)
class PlantSetupResult:
    """The plant and its initial location-history record."""

    plant: Plant
    location: PlantLocationHistory


def _required_text(value: str, *, field_name: str) -> str:
    """Remove surrounding whitespace and reject empty text."""

    cleaned_value = value.strip()

    if not cleaned_value:
        raise PlantSetupError(f"{field_name} is required.")

    return cleaned_value


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values."""

    if value is None:
        return None

    cleaned_value = value.strip()
    return cleaned_value or None


def _generate_plant_code(
    session: Session,
    *,
    household_id: UUID,
) -> str:
    """Generate the next readable plant code for a household."""

    existing_codes = set(
        session.scalars(
            select(Plant.plant_code).where(
                Plant.household_id == household_id
            )
        ).all()
    )

    number = 1

    while True:
        candidate = f"PLANT-{number:04d}"

        if candidate not in existing_codes:
            return candidate

        number += 1


def create_plant_with_location(
    session: Session,
    *,
    household_id: UUID,
    zone_id: UUID,
    nickname: str,
    species_id: UUID | None = None,
    cultivar_name: str | None = None,
    status: PlantStatus = PlantStatus.ACTIVE,
    identification_status: IdentificationStatus = (
        IdentificationStatus.UNCONFIRMED
    ),
    identification_confidence: Decimal | None = None,
    acquired_on: date | None = None,
    acquisition_source: str | None = None,
    parent_plant_id: UUID | None = None,
    location_started_at: datetime | None = None,
    placement_label: str | None = None,
    notes: str | None = None,
) -> PlantSetupResult:
    """Create a plant and assign its first environmental zone."""

    clean_nickname = _required_text(
        nickname,
        field_name="Plant name",
    )
    clean_cultivar_name = _optional_text(cultivar_name)
    clean_acquisition_source = _optional_text(acquisition_source)
    clean_placement_label = _optional_text(placement_label)
    clean_notes = _optional_text(notes)

    if identification_confidence is not None and not (
        Decimal(0)
        <= identification_confidence
        <= Decimal(1)
    ):
        raise PlantSetupError(
            "Identification confidence must be between 0 and 1."
        )

    household = session.get(Household, household_id)

    if household is None:
        raise PlantSetupError("The selected household does not exist.")

    zone = session.get(EnvironmentalZone, zone_id)

    if zone is None or not zone.active:
        raise PlantSetupError(
            "The selected plant-placement zone is not available."
        )

    space = session.get(Space, zone.space_id)

    if space is None or not space.active:
        raise PlantSetupError(
            "The selected zone does not belong to an active space."
        )

    site = session.get(Site, space.site_id)

    if (
        site is None
        or not site.active
        or site.household_id != household_id
    ):
        raise PlantSetupError(
            "The selected zone does not belong to this household."
        )

    if species_id is not None:
        species = session.get(Species, species_id)

        if species is None or not species.active:
            raise PlantSetupError(
                "The selected species is not available."
            )

    if parent_plant_id is not None:
        parent_plant = session.get(Plant, parent_plant_id)

        if (
            parent_plant is None
            or parent_plant.household_id != household_id
        ):
            raise PlantSetupError(
                "The parent plant does not belong to this household."
            )

    plant = Plant(
        household_id=household_id,
        species_id=species_id,
        parent_plant_id=parent_plant_id,
        plant_code=_generate_plant_code(
            session,
            household_id=household_id,
        ),
        nickname=clean_nickname,
        cultivar_name=clean_cultivar_name,
        status=status,
        identification_status=identification_status,
        identification_confidence=identification_confidence,
        acquired_on=acquired_on,
        acquisition_source=clean_acquisition_source,
        notes=clean_notes,
    )

    try:
        session.add(plant)
        session.flush()

        location = PlantLocationHistory(
            plant_id=plant.id,
            zone_id=zone.id,
            started_at=location_started_at or utc_now(),
            reason=LocationChangeReason.INITIAL_PLACEMENT,
            placement_label=clean_placement_label,
        )
        session.add(location)

        session.commit()
        session.refresh(plant)
        session.refresh(location)
    except IntegrityError as error:
        session.rollback()
        raise PlantSetupError(
            "The plant and its initial location could not be saved."
        ) from error
    except Exception:
        session.rollback()
        raise

    return PlantSetupResult(
        plant=plant,
        location=location,
    )