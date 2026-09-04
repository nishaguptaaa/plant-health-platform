"""Tests for plant-care recommendations and outcomes."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    Recommendation,
    RecommendationOutcome,
    RecommendationResult,
    RecommendationSource,
    RecommendationStatus,
    RecommendationType,
)


def test_recommendation_and_outcome_record_feedback_loop() -> None:
    """A recommendation and its measured result should retain key details."""

    recommendation_id = uuid4()
    generated_at = datetime.now(UTC)

    recommendation = Recommendation(
        household_id=uuid4(),
        plant_id=uuid4(),
        generated_at=generated_at,
        recommendation_type=RecommendationType.MOVE_TO_DIFFERENT_LIGHT,
        status=RecommendationStatus.PROPOSED,
        source=RecommendationSource.RULE_ENGINE,
        title="Move closer to brighter indirect light",
        rationale="Recent observations show slower growth in the current zone.",
        action_description="Move the plant to the east-window shelf.",
        expected_outcome="Improved new-leaf production.",
        confidence=Decimal("0.8300"),
    )

    outcome = RecommendationOutcome(
        recommendation_id=recommendation_id,
        assessed_at=generated_at,
        result=RecommendationResult.IMPROVED,
        health_score_before=Decimal("6.50"),
        health_score_after=Decimal("8.00"),
        follow_up_days=30,
        observed_changes="Two healthy new leaves emerged.",
    )

    assert recommendation.recommendation_type == (
        RecommendationType.MOVE_TO_DIFFERENT_LIGHT
    )
    assert recommendation.confidence == Decimal("0.8300")
    assert outcome.recommendation_id == recommendation_id
    assert outcome.result == RecommendationResult.IMPROVED
    assert outcome.health_score_after == Decimal("8.00")


def test_recommendation_models_have_validation_constraints() -> None:
    """Recommendation confidence, dates, and outcomes should be constrained."""

    recommendation_constraints = {
        constraint.name
        for constraint in Recommendation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    outcome_constraints = {
        constraint.name
        for constraint in RecommendationOutcome.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert (
        "ck_recommendations_valid_recommendation_confidence"
        in recommendation_constraints
    )
    assert (
        "ck_recommendations_valid_recommendation_expiration"
        in recommendation_constraints
    )
    assert (
        "ck_recommendation_outcomes_valid_outcome_health_score_before"
        in outcome_constraints
    )
    assert (
        "ck_recommendation_outcomes_valid_outcome_follow_up_days"
        in outcome_constraints
    )