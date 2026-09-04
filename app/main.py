"""Streamlit entry point for the Plant Health Platform."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from plant_health.database import (
    create_database_engine,
    create_session_factory,
)
from plant_health.database.models import (
    HealthIssue,
    HealthIssueStatus,
    Plant,
    Task,
    TaskStatus,
    WeatherSnapshot,
)
from plant_health.services import (
    HouseholdSetupError,
    create_household_with_owner,
)


@dataclass(frozen=True, slots=True)
class DashboardCounts:
    """Summary values displayed on the dashboard."""

    plants: int
    open_tasks: int
    active_health_issues: int
    weather_snapshots: int


@st.cache_resource
def get_session_factory() -> sessionmaker:
    """Create one reusable database session factory."""

    engine = create_database_engine()
    return create_session_factory(engine)


@st.cache_data(ttl=30)
def load_dashboard_counts() -> DashboardCounts | None:
    """Load dashboard counts, or return None if migrations are missing."""

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            plants = session.scalar(
                select(func.count(Plant.id))
            ) or 0
            open_tasks = session.scalar(
                select(func.count(Task.id)).where(
                    Task.status.in_(
                        [
                            TaskStatus.PENDING,
                            TaskStatus.IN_PROGRESS,
                        ]
                    )
                )
            ) or 0
            active_health_issues = session.scalar(
                select(func.count(HealthIssue.id)).where(
                    HealthIssue.status != HealthIssueStatus.RESOLVED
                )
            ) or 0
            weather_snapshots = session.scalar(
                select(func.count(WeatherSnapshot.id))
            ) or 0
    except SQLAlchemyError:
        return None

    return DashboardCounts(
        plants=plants,
        open_tasks=open_tasks,
        active_health_issues=active_health_issues,
        weather_snapshots=weather_snapshots,
    )


def render_dashboard() -> None:
    """Display summary counts and the current platform foundation."""

    counts = load_dashboard_counts()

    if counts is None:
        st.warning(
            "The database is not ready. Run "
            "`python -m alembic upgrade head` in the VS Code terminal."
        )
    else:
        plant_column, task_column, issue_column, weather_column = st.columns(4)

        plant_column.metric("Plants", counts.plants)
        task_column.metric("Open tasks", counts.open_tasks)
        issue_column.metric(
            "Active health issues",
            counts.active_health_issues,
        )
        weather_column.metric(
            "Weather snapshots",
            counts.weather_snapshots,
        )

    st.subheader("Current foundation")

    st.markdown(
        """
- Multi-user households and multiple sites
- Rooms, environmental zones, windows, skylights, and grow lights
- Individual plants, species, containers, substrates, and water culture
- Longitudinal observations, care, health issues, and treatments
- Tasks, recommendations, and measured outcomes
- Weather tracking, environmental measurements, and light estimation
"""
    )

    st.info(
        "Use Initial setup to create your first local user and household."
    )


def render_initial_setup() -> None:
    """Display the initial user and household form."""

    st.subheader("Create a household")
    st.write(
        "A household is the private boundary containing your family, "
        "sites, and plants."
    )
    st.caption(
        "This information is stored only in your local SQLite database. "
        "The application does not email you or upload these values."
    )

    with st.form("household_setup_form"):
        display_name = st.text_input(
            "Display name",
            placeholder="Your name",
        )
        email = st.text_input(
            "Email",
            placeholder="name@example.com",
            help=(
                "Used as a unique local account identifier. "
                "It is not used to send email."
            ),
        )
        household_name = st.text_input(
            "Household name",
            placeholder="My Household",
        )
        submitted = st.form_submit_button(
            "Create household",
            type="primary",
        )

    if not submitted:
        return

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            result = create_household_with_owner(
                session,
                display_name=display_name,
                email=email,
                household_name=household_name,
            )
    except HouseholdSetupError as error:
        st.error(str(error))
    except SQLAlchemyError:
        st.error(
            "The household could not be saved. Confirm that the "
            "database migrations are current."
        )
    else:
        load_dashboard_counts.clear()
        st.success(
            f"Created {result.household.name!r} with "
            f"{result.user.display_name!r} as the owner."
        )
        st.write(
            "Next, you can add the household's first site, such as a "
            "house, apartment, office, or greenhouse."
        )


st.set_page_config(
    page_title="Plant Health Platform",
    page_icon="🌿",
    layout="wide",
)

st.title("🌿 Plant Health Platform")
st.caption(
    "A local-first system for tracking plant care, environment, "
    "health, and growth."
)

dashboard_tab, setup_tab = st.tabs(
    [
        "Dashboard",
        "Initial setup",
    ]
)

with dashboard_tab:
    render_dashboard()

with setup_tab:
    render_initial_setup()