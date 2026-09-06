"""Read services for displaying the saved plant collection."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    IdentificationStatus,
    Plant,
    PlantLocationHistory,
    PlantStatus,
    Site,
    Space,
    Species,
)


@dataclass(frozen=True, slots=True)
class PlantCollectionItem:
    """One individual plant displayed in the collection."""

    id: UUID
    household_id: UUID
    household_name: str
    plant_code: str
    nickname: str | None
    cultivar_name: str | None
    status: PlantStatus
    identification_status: IdentificationStatus
    identification_confidence: Decimal | None
    scientific_name: str | None
    common_name: str | None
    acquired_on: date | None
    acquisition_source: str | None
    deceased_on: date | None
    notes: str | None
    zone_id: UUID | None
    site_name: str | None
    space_name: str | None
    zone_name: str | None


def load_plant_collection(
    session: Session,
    *,
    household_ids: Sequence[UUID] | None = None,
) -> list[PlantCollectionItem]:
    """Load plants with their species and current placement."""

    if household_ids is not None and not household_ids:
        return []

    statement = (
        select(
            Plant.id,
            Plant.household_id,
            Household.name.label("household_name"),
            Plant.plant_code,
            Plant.nickname,
            Plant.cultivar_name,
            Plant.status,
            Plant.identification_status,
            Plant.identification_confidence,
            Species.scientific_name,
            Species.primary_common_name.label("common_name"),
            Plant.acquired_on,
            Plant.acquisition_source,
            Plant.deceased_on,
            Plant.notes,
            EnvironmentalZone.id.label("zone_id"),
            Site.name.label("site_name"),
            Space.name.label("space_name"),
            EnvironmentalZone.name.label("zone_name"),
        )
        .join(
            Household,
            Plant.household_id == Household.id,
        )
        .outerjoin(
            Species,
            Plant.species_id == Species.id,
        )
        .outerjoin(
            PlantLocationHistory,
            and_(
                PlantLocationHistory.plant_id == Plant.id,
                PlantLocationHistory.ended_at.is_(None),
            ),
        )
        .outerjoin(
            EnvironmentalZone,
            PlantLocationHistory.zone_id == EnvironmentalZone.id,
        )
        .outerjoin(
            Space,
            EnvironmentalZone.space_id == Space.id,
        )
        .outerjoin(
            Site,
            Space.site_id == Site.id,
        )
        .order_by(
            Household.name,
            Plant.nickname,
            Plant.plant_code,
        )
    )

    if household_ids is not None:
        statement = statement.where(
            Plant.household_id.in_(household_ids)
        )

    rows = session.execute(statement).all()

    return [
        PlantCollectionItem(
            id=row.id,
            household_id=row.household_id,
            household_name=row.household_name,
            plant_code=row.plant_code,
            nickname=row.nickname,
            cultivar_name=row.cultivar_name,
            status=row.status,
            identification_status=row.identification_status,
            identification_confidence=row.identification_confidence,
            scientific_name=row.scientific_name,
            common_name=row.common_name,
            acquired_on=row.acquired_on,
            acquisition_source=row.acquisition_source,
            deceased_on=row.deceased_on,
            notes=row.notes,
            zone_id=row.zone_id,
            site_name=row.site_name,
            space_name=row.space_name,
            zone_name=row.zone_name,
        )
        for row in rows
    ]