"""Tests for plant-care task creation and lifecycle actions."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from plant_health.database import Base, create_database_engine
from plant_health.database.models import (
    CareEventType,
    EnvironmentalZone,
    Household,
    Site,
    SiteType,
    Space,
    SpaceType,
    TaskStatus,
    TaskType,
    ZoneType,
)
from plant_health.services import (
    TaskActionError,
    complete_task,
    create_plant_with_location,
    create_task,
    load_care_history,
    skip_task,
    snooze_task,
)


def _create_plant(session: Session) -> tuple[UUID, UUID]:
    """Create one plant in one household, and return their IDs."""

    household = Household(name="Test Household")
    session.add(household)
    session.flush()

    site = Site(
        household_id=household.id,
        name="Test Home",
        site_type=SiteType.HOUSE,
        timezone="America/New_York",
        weather_enabled=False,
    )
    session.add(site)
    session.flush()

    space = Space(
        site_id=site.id,
        name="Living Room",
        space_type=SpaceType.ROOM,
    )
    session.add(space)
    session.flush()

    zone = EnvironmentalZone(
        space_id=space.id,
        name="Window Shelf",
        zone_type=ZoneType.SHELF,
    )
    session.add(zone)
    session.commit()

    result = create_plant_with_location(
        session,
        household_id=household.id,
        zone_id=zone.id,
        nickname="Leafy",
    )

    return household.id, result.plant.id


def test_create_task_saves_pending_task() -> None:
    """A new task should be created with pending status."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Water Leafy",
            task_type=TaskType.WATER,
            plant_id=plant_id,
            due_at=datetime(2026, 3, 1, tzinfo=UTC),
        )

        assert task.status == TaskStatus.PENDING
        assert task.plant_id == plant_id


def test_create_task_rejects_plant_from_another_household() -> None:
    """A task cannot be created against another household's plant."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        _, plant_id = _create_plant(session)

        other_household = Household(name="Other Household")
        session.add(other_household)
        session.commit()

        with pytest.raises(
            TaskActionError,
            match="does not belong to this household",
        ):
            create_task(
                session,
                household_id=other_household.id,
                title="Water Leafy",
                task_type=TaskType.WATER,
                plant_id=plant_id,
            )


def test_complete_task_logs_matching_care_event() -> None:
    """Completing a watering task should record a real care event."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Water Leafy",
            task_type=TaskType.WATER,
            plant_id=plant_id,
        )

        completed_task = complete_task(
            session,
            household_id=household_id,
            task_id=task.id,
        )

        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None

        history = load_care_history(
            session,
            household_id=household_id,
            plant_id=plant_id,
        )

        assert len(history) == 1
        assert history[0].event_type == CareEventType.WATERING


def test_complete_task_without_care_mapping_skips_care_event() -> None:
    """Completing a task like INSPECT should not create a care event."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Check on Leafy",
            task_type=TaskType.INSPECT,
            plant_id=plant_id,
        )

        complete_task(
            session,
            household_id=household_id,
            task_id=task.id,
        )

        history = load_care_history(
            session,
            household_id=household_id,
            plant_id=plant_id,
        )

        assert history == []


def test_complete_recurring_task_schedules_next_occurrence() -> None:
    """Completing a repeating task should create the next pending task."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Water Leafy",
            task_type=TaskType.WATER,
            plant_id=plant_id,
            repeat_interval_days=7,
        )

        completed_task = complete_task(
            session,
            household_id=household_id,
            task_id=task.id,
        )

        from sqlalchemy import select

        from plant_health.database.models import Task

        pending_tasks = list(
            session.scalars(
                select(Task).where(Task.status == TaskStatus.PENDING)
            ).all()
        )

        expected_due_at = completed_task.completed_at + timedelta(days=7)

        assert len(pending_tasks) == 1
        assert pending_tasks[0].due_at == expected_due_at
        assert pending_tasks[0].repeat_interval_days == 7


def test_complete_task_rejects_already_completed_task() -> None:
    """A task that is already completed cannot be completed again."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Water Leafy",
            task_type=TaskType.WATER,
            plant_id=plant_id,
        )

        complete_task(session, household_id=household_id, task_id=task.id)

        with pytest.raises(
            TaskActionError,
            match="Only a pending task can be completed",
        ):
            complete_task(session, household_id=household_id, task_id=task.id)


def test_snooze_task_pushes_due_date_forward() -> None:
    """Snoozing should update the due date to a later time."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Water Leafy",
            task_type=TaskType.WATER,
            plant_id=plant_id,
            due_at=datetime(2026, 3, 1, tzinfo=UTC),
        )

        new_due_at = datetime.now(UTC) + timedelta(days=3)

        snoozed_task = snooze_task(
            session,
            household_id=household_id,
            task_id=task.id,
            new_due_at=new_due_at,
        )

        assert snoozed_task.due_at == new_due_at.replace(tzinfo=None)
        assert snoozed_task.status == TaskStatus.PENDING


def test_snooze_task_rejects_past_due_date() -> None:
    """Snoozing to a time in the past should be rejected."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Water Leafy",
            task_type=TaskType.WATER,
            plant_id=plant_id,
        )

        with pytest.raises(
            TaskActionError,
            match="must be in the future",
        ):
            snooze_task(
                session,
                household_id=household_id,
                task_id=task.id,
                new_due_at=datetime(2020, 1, 1, tzinfo=UTC),
            )


def test_skip_task_records_reason() -> None:
    """Skipping a task should mark it skipped and store the reason."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        household_id, plant_id = _create_plant(session)

        task = create_task(
            session,
            household_id=household_id,
            title="Water Leafy",
            task_type=TaskType.WATER,
            plant_id=plant_id,
        )

        skipped_task = skip_task(
            session,
            household_id=household_id,
            task_id=task.id,
            reason="Soil still damp from last week",
        )

        assert skipped_task.status == TaskStatus.SKIPPED
        assert skipped_task.notes == "Soil still damp from last week"
