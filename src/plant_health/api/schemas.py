"""Pydantic response models for the API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from plant_health.database.models import IdentificationStatus, PlantStatus


class PlantCollectionItemOut(BaseModel):
    """API representation of one plant in the collection."""

    model_config = ConfigDict(from_attributes=True)

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
