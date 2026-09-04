"""Tests for actionable plant-care tasks."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    Task,
    TaskPriority,
    TaskSource,
    TaskStatus,
    TaskType,
)


def test_task_records_future_care_action() -> None:
    """A task should store its target, deadline, and priority."""

    household_id = uuid4()
    plant_id = uuid4()
    due_at = datetime.now(UTC)

    task = Task(
        household_id=household_id,
        plant_id=plant_id,
        title="Inspect leaves for spider mites",
        task_type=TaskType.INSPECT,
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        source=TaskSource.MANUAL,
        due_at=due_at,
        repeat_interval_days=7,
    )

    assert task.household_id == household_id
    assert task.plant_id == plant_id
    assert task.task_type == TaskType.INSPECT
    assert task.priority == TaskPriority.HIGH
    assert task.due_at == due_at
    assert task.repeat_interval_days == 7


def test_task_has_validation_constraints() -> None:
    """Task recurrence and completion dates should be constrained."""

    constraint_names = {
        constraint.name
        for constraint in Task.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_tasks_valid_task_repeat_interval" in constraint_names
    assert "ck_tasks_valid_task_completion_date" in constraint_names