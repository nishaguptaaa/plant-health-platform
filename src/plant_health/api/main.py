"""FastAPI entry point for the Plant Health Platform API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from plant_health.api.dependencies import get_db
from plant_health.api.schemas import (
    CareEventCreate,
    CareEventOut,
    PlantCollectionItemOut,
)
from plant_health.services import CareRecordingError, record_care_event
from plant_health.services.plant_collection import load_plant_collection

app = FastAPI(title="Plant Health Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DbSession = Annotated[Session, Depends(get_db)]


@app.get("/health")
def health_check() -> dict[str, str]:
    """Confirm the API process is running."""

    return {"status": "ok"}


@app.get("/plants", response_model=list[PlantCollectionItemOut])
def list_plants(session: DbSession) -> list[PlantCollectionItemOut]:
    """Return every plant in the collection, across all households, for now."""

    return load_plant_collection(session)


@app.post("/care-events", response_model=CareEventOut, status_code=201)
def create_care_event(
    payload: CareEventCreate,
    session: DbSession,
) -> CareEventOut:
    """Record a care event for a plant."""

    try:
        return record_care_event(
            session,
            household_id=payload.household_id,
            plant_id=payload.plant_id,
            event_type=payload.event_type,
            occurred_at=payload.occurred_at,
            performed_by_user_id=payload.performed_by_user_id,
            source=payload.source,
            amount_ml=payload.amount_ml,
            fertilizer_name=payload.fertilizer_name,
            fertilizer_dilution_ratio=payload.fertilizer_dilution_ratio,
            water_ph=payload.water_ph,
            water_ec_ms_cm=payload.water_ec_ms_cm,
            product_name=payload.product_name,
            notes=payload.notes,
        )
    except CareRecordingError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
