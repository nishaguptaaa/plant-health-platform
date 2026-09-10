"""FastAPI entry point for the Plant Health Platform API."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from plant_health.api.dependencies import get_db
from plant_health.api.schemas import (
    CareEventCreate,
    CareEventOut,
    PlantCollectionItemOut,
    TaskCompleteRequest,
    TaskCreate,
    TaskOut,
    TaskSkipRequest,
    TaskSnoozeRequest,
)
from plant_health.database.models import TaskStatus
from plant_health.services import (
    CareRecordingError,
    TaskActionError,
    complete_task,
    create_task,
    load_care_history,
    load_tasks,
    record_care_event,
    skip_task,
    snooze_task,
)
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
            watering_method=payload.watering_method,
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


@app.get(
    "/plants/{plant_id}/care-events",
    response_model=list[CareEventOut],
)
def list_care_events(
    plant_id: UUID,
    household_id: UUID,
    session: DbSession,
) -> list[CareEventOut]:
    """Return a plant's recorded care events, most recent first."""

    try:
        return load_care_history(
            session,
            household_id=household_id,
            plant_id=plant_id,
        )
    except CareRecordingError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_new_task(
    payload: TaskCreate,
    session: DbSession,
) -> TaskOut:
    """Create a new plant-care task."""

    try:
        return create_task(
            session,
            household_id=payload.household_id,
            title=payload.title,
            task_type=payload.task_type,
            plant_id=payload.plant_id,
            due_at=payload.due_at,
            repeat_interval_days=payload.repeat_interval_days,
            priority=payload.priority,
            source=payload.source,
            assigned_to_user_id=payload.assigned_to_user_id,
            description=payload.description,
            notes=payload.notes,
        )
    except TaskActionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/tasks", response_model=list[TaskOut])
def list_household_tasks(
    household_id: UUID,
    session: DbSession,
    status: TaskStatus | None = None,
) -> list[TaskOut]:
    """Return a household's tasks, optionally filtered by status."""

    return load_tasks(session, household_id=household_id, status=status)


@app.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_existing_task(
    task_id: UUID,
    payload: TaskCompleteRequest,
    session: DbSession,
) -> TaskOut:
    """Complete a task, logging a matching care event when applicable."""

    try:
        return complete_task(
            session,
            household_id=payload.household_id,
            task_id=task_id,
            completed_at=payload.completed_at,
            performed_by_user_id=payload.performed_by_user_id,
            watering_method=payload.watering_method,
            amount_ml=payload.amount_ml,
            fertilizer_name=payload.fertilizer_name,
            fertilizer_dilution_ratio=payload.fertilizer_dilution_ratio,
            water_ph=payload.water_ph,
            water_ec_ms_cm=payload.water_ec_ms_cm,
            product_name=payload.product_name,
            notes=payload.notes,
        )
    except TaskActionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/tasks/{task_id}/snooze", response_model=TaskOut)
def snooze_existing_task(
    task_id: UUID,
    payload: TaskSnoozeRequest,
    session: DbSession,
) -> TaskOut:
    """Push a task's due date to a later time."""

    try:
        return snooze_task(
            session,
            household_id=payload.household_id,
            task_id=task_id,
            new_due_at=payload.new_due_at,
        )
    except TaskActionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/tasks/{task_id}/skip", response_model=TaskOut)
def skip_existing_task(
    task_id: UUID,
    payload: TaskSkipRequest,
    session: DbSession,
) -> TaskOut:
    """Skip a task, optionally recording why."""

    try:
        return skip_task(
            session,
            household_id=payload.household_id,
            task_id=task_id,
            reason=payload.reason,
        )
    except TaskActionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
