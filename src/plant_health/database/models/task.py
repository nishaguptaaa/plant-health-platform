"""Actionable plant-care tasks."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from plant_health.database.base import Base
from plant_health.database.models.common import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from plant_health.database.models.health import HealthIssue
    from plant_health.database.models.identity import Household, User
    from plant_health.database.models.plant import Plant


class TaskType(StrEnum):
    """Kinds of plant-care tasks."""

    WATER = "water"
    CHANGE_WATER = "change_water"
    TOP_OFF_WATER = "top_off_water"
    INSPECT = "inspect"
    TREAT = "treat"
    MOVE = "move"
    REPOT = "repot"
    FERTILIZE = "fertilize"
    PRUNE = "prune"
    CLEAN = "clean"
    ROTATE = "rotate"
    PHOTOGRAPH = "photograph"
    MEASURE = "measure"
    OTHER = "other"


class TaskStatus(StrEnum):
    """Current state of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    """Urgency assigned to a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskSource(StrEnum):
    """Origin of a task."""

    MANUAL = "manual"
    RECOMMENDATION = "recommendation"
    RULE_ENGINE = "rule_engine"
    NLP_ASSISTANT = "nlp_assistant"
    SYSTEM = "system"
    IMPORTED = "imported"


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A care action that may be assigned and completed later."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "repeat_interval_days IS NULL OR repeat_interval_days > 0",
            name="valid_task_repeat_interval",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name="valid_task_completion_date",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    health_issue_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("health_issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    task_type: Mapped[TaskType] = mapped_column(
        Enum(
            TaskType,
            name="task_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(
            TaskPriority,
            name="task_priority",
            native_enum=False,
            validate_strings=True,
        ),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    source: Mapped[TaskSource] = mapped_column(
        Enum(
            TaskSource,
            name="task_source",
            native_enum=False,
            validate_strings=True,
        ),
        default=TaskSource.MANUAL,
        nullable=False,
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    repeat_interval_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    household: Mapped[Household] = relationship()
    plant: Mapped[Plant | None] = relationship()
    health_issue: Mapped[HealthIssue | None] = relationship()
    assigned_to_user: Mapped[User | None] = relationship(
        foreign_keys=[assigned_to_user_id],
    )
    created_by_user: Mapped[User | None] = relationship(
        foreign_keys=[created_by_user_id],
    )