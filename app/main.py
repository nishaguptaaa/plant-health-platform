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
    "Next, we will add forms for entering your first household, site, "
    "rooms, zones, and plants."
)