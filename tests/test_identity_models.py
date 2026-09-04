"""Tests for users, households, and memberships."""

from sqlalchemy import select

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


def test_user_can_join_household() -> None:
    """A user should be assignable to a household with a role."""

    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine)
    Base.metadata.create_all(engine)

    user = User(
        email="user@example.com",
        display_name="Example User",
    )
    household = Household(name="Example Household")
    membership = HouseholdMembership(
        user=user,
        household=household,
        role=HouseholdRole.OWNER,
    )

    with session_factory() as session:
        session.add(membership)
        session.commit()

        saved_membership = session.scalar(
            select(HouseholdMembership).where(
                HouseholdMembership.user_id == user.id
            )
        )

        assert saved_membership is not None
        assert saved_membership.role == HouseholdRole.OWNER
        assert saved_membership.household.name == "Example Household"
        assert saved_membership.user.display_name == "Example User"

    Base.metadata.drop_all(engine)
    engine.dispose()