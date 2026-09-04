"""Tests for longitudinal plant observations."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    ObservationSource,
    ObservationType,
    PlantObservation,
)


def test_plant_observation_records_health_snapshot() -> None:
    """A plant observation should store structured health information."""

    observed_at = datetime.now(UTC)
    plant_id = uuid4()

    observation = PlantObservation(
        plant_id=plant_id,
        observed_at=observed_at,
        observation_type=ObservationType.HEALTH_CHECK,
        source=ObservationSource.MANUAL,
        overall_health_score=Decimal("8.25"),
        leaf_count=12,
        new_leaf_count=2,
        yellow_leaf_count=1,
        damaged_leaf_count=0,
        height_cm=Decimal("42.50"),
        canopy_width_cm=Decimal("31.25"),
        visible_pests=False,
        flowering=False,
        summary="Healthy overall with one yellow leaf.",
        confidence=Decimal("0.9500"),
        human_verified=True,
    )

    assert observation.plant_id == plant_id
    assert observation.observed_at == observed_at
    assert observation.overall_health_score == Decimal("8.25")
    assert observation.new_leaf_count == 2
    assert observation.visible_pests is False
    assert observation.human_verified is True


def test_plant_observation_has_validation_constraints() -> None:
    """Health scores, confidence, and measurements should be constrained."""

    constraint_names = {
        constraint.name
        for constraint in PlantObservation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_plant_observations_valid_overall_health_score" in constraint_names
    assert "ck_plant_observations_valid_observation_confidence" in constraint_names
    assert "ck_plant_observations_valid_leaf_count" in constraint_names
    assert "ck_plant_observations_valid_plant_height" in constraint_names