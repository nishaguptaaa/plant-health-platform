"""Tests for plant health issues."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint

from plant_health.database.models import (
    HealthIssue,
    HealthIssueCategory,
    HealthIssueSource,
    HealthIssueStatus,
)


def test_health_issue_records_suspected_problem() -> None:
    """A suspected health issue should retain structured details."""

    plant_id = uuid4()
    detected_at = datetime.now(UTC)

    issue = HealthIssue(
        plant_id=plant_id,
        title="Possible spider mites",
        category=HealthIssueCategory.PEST,
        status=HealthIssueStatus.SUSPECTED,
        source=HealthIssueSource.PHOTO_AI,
        detected_at=detected_at,
        severity_score=2,
        affected_area="Undersides of three leaves",
        confidence=Decimal("0.7200"),
        human_verified=False,
    )

    assert issue.plant_id == plant_id
    assert issue.category == HealthIssueCategory.PEST
    assert issue.status == HealthIssueStatus.SUSPECTED
    assert issue.severity_score == 2
    assert issue.confidence == Decimal("0.7200")


def test_health_issue_has_validation_constraints() -> None:
    """Issue severity, confidence, and dates should be constrained."""

    constraint_names = {
        constraint.name
        for constraint in HealthIssue.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_health_issues_valid_health_issue_severity" in constraint_names
    assert "ck_health_issues_valid_health_issue_confidence" in constraint_names
    assert "ck_health_issues_valid_health_issue_dates" in constraint_names