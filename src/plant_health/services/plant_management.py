"""Services for editing existing plant records and identification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    IdentificationStatus,
    Plant,
    PlantStatus,
    Species,
)


class PlantManagementError(ValueError):
    """Raised when an existing plant cannot be updated."""


@dataclass(frozen=True, slots=True)
class PlantManagementResult:
    """The updated plant and its assigned species, when identified."""

    plant: Plant
    species: Species | None


def _required_text(value: str, *, field_name: str) -> str:
    """Remove surrounding whitespace and reject empty text."""

    cleaned_value = value.strip()

    if not cleaned_value:
        raise PlantManagementError(f"{field_name} is required.")

    return cleaned_value


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values."""

    if value is None:
        return None

    cleaned_value = value.strip()
    return cleaned_value or None


def _find_or_create_species(
    session: Session,
    *,
    scientific_name: str,
    common_name: str | None,
    identification_status: IdentificationStatus,
) -> Species:
    """Return an existing species or create a new reference record."""

    species = session.scalar(
        select(Species).where(
            func.lower(Species.scientific_name)
            == scientific_name.casefold()
        )
    )

    if species is not None:
        if not species.active:
            raise PlantManagementError(
                "The matching species record is inactive."
            )

        if (
            species.primary_common_name is None
            and common_name is not None
        ):
            species.primary_common_name = common_name

        return species

    species = Species(
        scientific_name=scientific_name,
        primary_common_name=common_name,
        human_verified=identification_status
        in {
            IdentificationStatus.USER_CONFIRMED,
            IdentificationStatus.EXPERT_CONFIRMED,
        },
    )
    session.add(species)
    session.flush()

    return species


def update_plant_details(
    session: Session,
    *,
    household_id: UUID,
    plant_id: UUID,
    nickname: str,
    status: PlantStatus,
    scientific_name: str | None = None,
    common_name: str | None = None,
    cultivar_name: str | None = None,
    identification_status: IdentificationStatus = (
        IdentificationStatus.UNCONFIRMED
    ),
    identification_confidence: Decimal | None = None,
    acquired_on: date | None = None,
    acquisition_source: str | None = None,
    deceased_on: date | None = None,
    notes: str | None = None,
) -> PlantManagementResult:
    """Update a plant while protecting its household ownership."""

    clean_nickname = _required_text(
        nickname,
        field_name="Plant name",
    )
    clean_scientific_name = _optional_text(scientific_name)
    clean_common_name = _optional_text(common_name)
    clean_cultivar_name = _optional_text(cultivar_name)
    clean_acquisition_source = _optional_text(acquisition_source)
    clean_notes = _optional_text(notes)

    plant = session.get(Plant, plant_id)

    if plant is None or plant.household_id != household_id:
        raise PlantManagementError(
            "The selected plant does not belong to this household."
        )

    if identification_confidence is not None and not (
        Decimal(0)
        <= identification_confidence
        <= Decimal(1)
    ):
        raise PlantManagementError(
            "Identification confidence must be between 0 and 1."
        )

    today = datetime.now(UTC).date()

    if acquired_on is not None and acquired_on > today:
        raise PlantManagementError(
            "The acquisition date cannot be in the future."
        )

    if deceased_on is not None and deceased_on > today:
        raise PlantManagementError(
            "The deceased date cannot be in the future."
        )

    if (
        acquired_on is not None
        and deceased_on is not None
        and deceased_on < acquired_on
    ):
        raise PlantManagementError(
            "The deceased date cannot be before the acquisition date."
        )

    species: Species | None = None

    if clean_scientific_name is None:
        if clean_common_name is not None:
            raise PlantManagementError(
                "Enter a scientific name before adding a common name."
            )

        if (
            identification_status
            != IdentificationStatus.UNCONFIRMED
            or identification_confidence is not None
        ):
            raise PlantManagementError(
                "Enter a scientific name before recording identification "
                "status or confidence."
            )
    else:
        species = _find_or_create_species(
            session,
            scientific_name=clean_scientific_name,
            common_name=clean_common_name,
            identification_status=identification_status,
        )

    plant.nickname = clean_nickname
    plant.status = status
    plant.species_id = species.id if species is not None else None
    plant.cultivar_name = clean_cultivar_name
    plant.identification_status = identification_status
    plant.identification_confidence = identification_confidence
    plant.acquired_on = acquired_on
    plant.acquisition_source = clean_acquisition_source
    plant.deceased_on = deceased_on
    plant.notes = clean_notes

    try:
        session.commit()
        session.refresh(plant)

        if species is not None:
            session.refresh(species)
    except IntegrityError as error:
        session.rollback()
        raise PlantManagementError(
            "The plant details could not be saved."
        ) from error
    except Exception:
        session.rollback()
        raise

    return PlantManagementResult(
        plant=plant,
        species=species,
    )