"""Pydantic response models for the API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from plant_health.database.models import (
    CareEventSource,
    CareEventType,
    IdentificationStatus,
    PlantStatus,
    WateringMethod,
)


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


class CareEventCreate(BaseModel):
    """Request body for recording a new care event.

    ``household_id`` is required directly for now because there is no
    authenticated session yet to infer it from. Once real
    authentication exists, this should come from the logged-in user's
    active household instead of being supplied by the client.
    """

    household_id: UUID
    plant_id: UUID
    event_type: CareEventType
    occurred_at: datetime | None = None
    performed_by_user_id: UUID | None = None
    source: CareEventSource = CareEventSource.MANUAL
    watering_method: WateringMethod | None = None
    amount_ml: Decimal | None = None
    fertilizer_name: str | None = None
    fertilizer_dilution_ratio: Decimal | None = None
    water_ph: Decimal | None = None
    water_ec_ms_cm: Decimal | None = None
    product_name: str | None = None
    notes: str | None = None


class CareEventOut(BaseModel):
    """API representation of a saved care event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plant_id: UUID
    performed_by_user_id: UUID | None
    occurred_at: datetime
    event_type: CareEventType
    source: CareEventSource
    watering_method: WateringMethod | None
    amount_ml: Decimal | None
    fertilizer_name: str | None
    fertilizer_dilution_ratio: Decimal | None
    water_ph: Decimal | None
    water_ec_ms_cm: Decimal | None
    product_name: str | None
    notes: str | None
    created_at: datetime
