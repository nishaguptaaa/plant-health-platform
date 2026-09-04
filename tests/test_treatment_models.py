"""Tests for plant-health treatments."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    Treatment,
    TreatmentOutcome,
    TreatmentStatus,
)


def test_treatment_records_intervention_and_outcome() -> None:
    """A treatment should store its method, status, and result."""

    health_issue_id = uuid4()
    started_at = datetime.now(UTC)

    treatment = Treatment(
        health_issue_id=health_issue_id,
        treatment_name="Insecticidal soap treatment",
        status=TreatmentStatus.IN_PROGRESS,
        started_at=started_at,
        product_name="Insecticidal soap",
        application_method="Sprayed on both sides of affected leaves",
        frequency_description="Repeat every seven days",
        outcome=TreatmentOutcome.NOT_ASSESSED,
    )

    assert treatment.health_issue_id == health_issue_id
    assert treatment.started_at == started_at
    assert treatment.status == TreatmentStatus.IN_PROGRESS
    assert treatment.product_name == "Insecticidal soap"
    assert treatment.outcome == TreatmentOutcome.NOT_ASSESSED


def test_treatment_has_date_constraints() -> None:
    """Treatment completion and assessment dates should follow its start."""

    constraint_names = {
        constraint.name
        for constraint in Treatment.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_treatments_valid_treatment_dates" in constraint_names
    assert "ck_treatments_valid_treatment_outcome_date" in constraint_names