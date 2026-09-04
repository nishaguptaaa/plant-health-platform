"""Plant-care recommendations and measured outcomes."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
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
    from plant_health.database.models.identity import Household
    from plant_health.database.models.plant import Plant


class RecommendationType(StrEnum):
    """Kinds of recommendations the platform can make."""

    WATER_ADJUSTMENT = "water_adjustment"
    MOVE_TO_DIFFERENT_LIGHT = "move_to_different_light"
    ADJUST_GROW_LIGHT = "adjust_grow_light"
    REPOT = "repot"
    CHANGE_SUBSTRATE = "change_substrate"
    CHANGE_CULTIVATION_METHOD = "change_cultivation_method"
    FERTILIZE = "fertilize"
    TREAT_HEALTH_ISSUE = "treat_health_issue"
    ADJUST_HUMIDITY = "adjust_humidity"
    MONITOR = "monitor"
    KEEP_AS_IS = "keep_as_is"
    OTHER = "other"


class RecommendationStatus(StrEnum):
    """Current state of a recommendation."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class RecommendationSource(StrEnum):
    """Origin of a recommendation."""

    RULE_ENGINE = "rule_engine"
    ML_MODEL = "ml_model"
    AI_ASSISTANT = "ai_assistant"
    HUMAN_EXPERT = "human_expert"
    MANUAL = "manual"
    IMPORTED = "imported"


class RecommendationResult(StrEnum):
    """Observed result after following a recommendation."""

    NOT_ASSESSED = "not_assessed"
    IMPROVED = "improved"
    NO_CHANGE = "no_change"
    WORSENED = "worsened"
    MIXED = "mixed"


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A proposed action intended to improve or preserve plant health."""

    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="valid_recommendation_confidence",
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until >= generated_at",
            name="valid_recommendation_expiration",
        ),
        CheckConstraint(
            "accepted_at IS NULL OR accepted_at >= generated_at",
            name="valid_recommendation_acceptance_date",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= generated_at",
            name="valid_recommendation_completion_date",
        ),
    )

    household_id: Mapped[UUID] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plant_id: Mapped[UUID] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    health_issue_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("health_issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    recommendation_type: Mapped[RecommendationType] = mapped_column(
        Enum(
            RecommendationType,
            name="recommendation_type",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(
            RecommendationStatus,
            name="recommendation_status",
            native_enum=False,
            validate_strings=True,
        ),
        default=RecommendationStatus.PROPOSED,
        nullable=False,
    )
    source: Mapped[RecommendationSource] = mapped_column(
        Enum(
            RecommendationSource,
            name="recommendation_source",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    action_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    expected_outcome: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    household: Mapped[Household] = relationship()
    plant: Mapped[Plant] = relationship()
    health_issue: Mapped[HealthIssue | None] = relationship()
    outcomes: Mapped[list[RecommendationOutcome]] = relationship(
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )


class RecommendationOutcome(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A follow-up assessment of a recommendation's effectiveness."""

    __tablename__ = "recommendation_outcomes"
    __table_args__ = (
        CheckConstraint(
            "health_score_before IS NULL "
            "OR health_score_before BETWEEN 0 AND 10",
            name="valid_outcome_health_score_before",
        ),
        CheckConstraint(
            "health_score_after IS NULL "
            "OR health_score_after BETWEEN 0 AND 10",
            name="valid_outcome_health_score_after",
        ),
        CheckConstraint(
            "follow_up_days IS NULL OR follow_up_days >= 0",
            name="valid_outcome_follow_up_days",
        ),
        CheckConstraint(
            "baseline_observation_id IS NULL "
            "OR follow_up_observation_id IS NULL "
            "OR baseline_observation_id != follow_up_observation_id",
            name="different_outcome_observations",
        ),
    )

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    baseline_observation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plant_observations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    follow_up_observation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plant_observations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    result: Mapped[RecommendationResult] = mapped_column(
        Enum(
            RecommendationResult,
            name="recommendation_result",
            native_enum=False,
            validate_strings=True,
        ),
        default=RecommendationResult.NOT_ASSESSED,
        nullable=False,
    )
    health_score_before: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    health_score_after: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    follow_up_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    observed_changes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommendation: Mapped[Recommendation] = relationship(
        back_populates="outcomes",
    )