"""FastAPI entry point for the Plant Health Platform API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from plant_health.api.dependencies import get_db
from plant_health.api.schemas import PlantCollectionItemOut
from plant_health.services.plant_collection import load_plant_collection

app = FastAPI(title="Plant Health Platform API")

DbSession = Annotated[Session, Depends(get_db)]


@app.get("/health")
def health_check() -> dict[str, str]:
    """Confirm the API process is running."""

    return {"status": "ok"}


@app.get("/plants", response_model=list[PlantCollectionItemOut])
def list_plants(session: DbSession) -> list[PlantCollectionItemOut]:
    """Return every plant in the collection, across all households, for now."""

    return load_plant_collection(session)
