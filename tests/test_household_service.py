"""Tests for household setup services."""

import pytest
from sqlalchemy import func, select

from plant_health.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from plant_health.database.models import (
    Household,
    HouseholdMembership,
    HouseholdRole,
    User,
)
from plant_health.services import (
    HouseholdSetupError,
    create_household_with_owner,
)


def test_create_household_with_owner_creates_connected_records() -> None:
    """Initial setup should create a user, household, and owner membership."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        result = create_household_with_owner(
            session,
            display_name="Ashna",
            email="  ASHNA@example.com ",
            household_name="Shrewsbury Home",
        )

        assert result.user.email == "ashna@example.com"
        assert result.user.display_name == "Ashna"
        assert result.household.name == "Shrewsbury Home"
        assert result.membership.user_id == result.user.id
        assert result.membership.household_id == result.household.id
        assert result.membership.role == HouseholdRole.OWNER

        second_result = create_household_with_owner(
            session,
            display_name="Ashna",
            email="ashna@example.com",
            household_name="Future Apartment",
        )

        assert second_result.user.id == result.user.id
        assert session.scalar(select(func.count(User.id))) == 1
        assert session.scalar(select(func.count(Household.id))) == 2
        assert (
            session.scalar(select(func.count(HouseholdMembership.id)))
            == 2
        )

    engine.dispose()


def test_create_household_with_owner_validates_required_fields() -> None:
    """Invalid setup information should be rejected before database writes."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        with pytest.raises(
            HouseholdSetupError,
            match="Display name is required",
        ):
            create_household_with_owner(
                session,
                display_name=" ",
                email="ashna@example.com",
                household_name="Test Household",
            )

        with pytest.raises(
            HouseholdSetupError,
            match="Enter a valid email address",
        ):
            create_household_with_owner(
                session,
                display_name="Ashna",
                email="invalid-email",
                household_name="Test Household",
            )

        assert session.scalar(select(func.count(User.id))) == 0
        assert session.scalar(select(func.count(Household.id))) == 0

    engine.dispose()