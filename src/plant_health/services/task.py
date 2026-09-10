"""Services for managing plant-care tasks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    CareEventSource,
    CareEventType,
    Plant,
    Task,
    TaskPriority,
    TaskSource,
    TaskStatus,
    TaskType,
    WateringMethod,
)
from plant_health.database.models.common import utc_now
from plant_health.services.care import record_care_event


class TaskActionError(ValueError):
    """Raised when a task cannot be created or updated."""


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


_CARE_EVENT_TYPE_BY_TASK_TYPE: dict[TaskType, CareEventType] = {
    TaskType.WATER: CareEventType.WATERING,
    TaskType.CHANGE_WATER: CareEventType.WATER_CHANGE,
    TaskType.TOP_OFF_WATER: CareEventType.WATER_TOP_OFF,
    TaskType.FERTILIZE: CareEventType.FERTILIZING,
    TaskType.REPOT: CareEventType.REPOTTING,
    TaskType.PRUNE: CareEventType.PRUNING,
    TaskType.CLEAN: CareEventType.CLEANING,
    TaskType.ROTATE: CareEventType.ROTATING,
    TaskType.TREAT: CareEventType.PEST_TREATMENT,
}


def create_task(
    session: Session,
    *,
    household_id: UUID,
    title: str,
    task_type: TaskType,
    plant_id: UUID | None = None,
    due_at: datetime | None = None,
    repeat_interval_days: int | None = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    source: TaskSource = TaskSource.MANUAL,
    assigned_to_user_id: UUID | None = None,
    description: str | None = None,
    notes: str | None = None,
) -> Task:
    """Create a new plant-care task."""

    clean_title = _optional_text(title)

    if clean_title is None:
        raise TaskActionError("A task needs a title.")

    if plant_id is not None:
        plant = session.get(Plant, plant_id)

        if plant is None or plant.household_id != household_id:
            raise TaskActionError(
                "The selected plant does not belong to this household."
            )

    if repeat_interval_days is not None and repeat_interval_days <= 0:
        raise TaskActionError(
            "The repeat interval must be greater than zero."
        )

    task = Task(
        household_id=household_id,
        plant_id=plant_id,
        title=clean_title,
        description=_optional_text(description),
        task_type=task_type,
        status=TaskStatus.PENDING,
        priority=priority,
        source=source,
        due_at=due_at,
        repeat_interval_days=repeat_interval_days,
        assigned_to_user_id=assigned_to_user_id,
        notes=_optional_text(notes),
    )

    try:
        session.add(task)
        session.commit()
        session.refresh(task)
    except IntegrityError as error:
        session.rollback()
        raise TaskActionError("The task could not be created.") from error
    except Exception:
        session.rollback()
        raise

    return task


def complete_task(
    session: Session,
    *,
    household_id: UUID,
    task_id: UUID,
    completed_at: datetime | None = None,
    performed_by_user_id: UUID | None = None,
    watering_method: WateringMethod | None = None,
    amount_ml: Decimal | None = None,
    fertilizer_name: str | None = None,
    fertilizer_dilution_ratio: Decimal | None = None,
    water_ph: Decimal | None = None,
    water_ec_ms_cm: Decimal | None = None,
    product_name: str | None = None,
    notes: str | None = None,
) -> Task:
    """Mark a task complete, logging a matching care event when applicable.

    If the task repeats, the next occurrence is automatically scheduled.
    """

    task = session.get(Task, task_id)

    if task is None or task.household_id != household_id:
        raise TaskActionError(
            "The selected task does not belong to this household."
        )

    if task.status != TaskStatus.PENDING:
        raise TaskActionError("Only a pending task can be completed.")

    completion_time = completed_at or utc_now()

    if _as_utc(completion_time) > _as_utc(utc_now()):
        raise TaskActionError("The completion time cannot be in the future.")

    care_event_type = _CARE_EVENT_TYPE_BY_TASK_TYPE.get(task.task_type)

    if care_event_type is not None and task.plant_id is not None:
        record_care_event(
            session,
            household_id=household_id,
            plant_id=task.plant_id,
            event_type=care_event_type,
            occurred_at=completion_time,
            performed_by_user_id=performed_by_user_id,
            source=CareEventSource.MANUAL,
            watering_method=watering_method,
            amount_ml=amount_ml,
            fertilizer_name=fertilizer_name,
            fertilizer_dilution_ratio=fertilizer_dilution_ratio,
            water_ph=water_ph,
            water_ec_ms_cm=water_ec_ms_cm,
            product_name=product_name,
            notes=notes,
        )

    task.status = TaskStatus.COMPLETED
    task.completed_at = completion_time

    if task.repeat_interval_days is not None:
        next_due_at = completion_time + timedelta(
            days=task.repeat_interval_days
        )

        next_task = Task(
            household_id=task.household_id,
            plant_id=task.plant_id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=TaskStatus.PENDING,
            priority=task.priority,
            source=TaskSource.RULE_ENGINE,
            due_at=next_due_at,
            repeat_interval_days=task.repeat_interval_days,
            assigned_to_user_id=task.assigned_to_user_id,
        )
        session.add(next_task)

    try:
        session.commit()
        session.refresh(task)
    except IntegrityError as error:
        session.rollback()
        raise TaskActionError("The task could not be completed.") from error
    except Exception:
        session.rollback()
        raise

    return task


def snooze_task(
    session: Session,
    *,
    household_id: UUID,
    task_id: UUID,
    new_due_at: datetime,
) -> Task:
    """Push a pending task's due date to a later time."""

    task = session.get(Task, task_id)

    if task is None or task.household_id != household_id:
        raise TaskActionError(
            "The selected task does not belong to this household."
        )

    if task.status != TaskStatus.PENDING:
        raise TaskActionError("Only a pending task can be snoozed.")

    if _as_utc(new_due_at) <= _as_utc(utc_now()):
        raise TaskActionError("The new due date must be in the future.")

    task.due_at = new_due_at

    try:
        session.commit()
        session.refresh(task)
    except IntegrityError as error:
        session.rollback()
        raise TaskActionError("The task could not be snoozed.") from error
    except Exception:
        session.rollback()
        raise

    return task


def skip_task(
    session: Session,
    *,
    household_id: UUID,
    task_id: UUID,
    reason: str | None = None,
) -> Task:
    """Mark a pending task as skipped, optionally recording why."""

    task = session.get(Task, task_id)

    if task is None or task.household_id != household_id:
        raise TaskActionError(
            "The selected task does not belong to this household."
        )

    if task.status != TaskStatus.PENDING:
        raise TaskActionError("Only a pending task can be skipped.")

    task.status = TaskStatus.SKIPPED

    clean_reason = _optional_text(reason)
    if clean_reason is not None:
        task.notes = clean_reason

    try:
        session.commit()
        session.refresh(task)
    except IntegrityError as error:
        session.rollback()
        raise TaskActionError("The task could not be skipped.") from error
    except Exception:
        session.rollback()
        raise

    return task
