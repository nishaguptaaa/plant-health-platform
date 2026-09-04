"""Streamlit entry point for the Plant Health Platform."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

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
    Household,
    Plant,
    SiteType,
    Task,
    TaskStatus,
    TerrainPosition,
    WeatherSnapshot,
)
from plant_health.services import (
    HouseholdSetupError,
    SiteSetupError,
    create_household_with_owner,
    create_site,
)
from plant_health.weather import (
    GeocodingError,
    GeocodingResult,
    OpenMeteoGeocoder,
)


@dataclass(frozen=True, slots=True)
class DashboardCounts:
    """Summary values displayed on the dashboard."""

    plants: int
    open_tasks: int
    active_health_issues: int
    weather_snapshots: int


@dataclass(frozen=True, slots=True)
class HouseholdOption:
    """A household option displayed without exposing its database ID."""

    id: UUID
    name: str


@st.cache_resource
def get_session_factory() -> sessionmaker:
    """Create one reusable database session factory."""

    engine = create_database_engine()
    return create_session_factory(engine)


@st.cache_resource
def get_geocoder() -> OpenMeteoGeocoder:
    """Create one reusable location-search client."""

    return OpenMeteoGeocoder()


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


@st.cache_data(ttl=30)
def load_household_options() -> list[HouseholdOption]:
    """Load households for application selection controls."""

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            households = session.scalars(
                select(Household).order_by(Household.name)
            ).all()
    except SQLAlchemyError:
        return []

    return [
        HouseholdOption(
            id=household.id,
            name=household.name,
        )
        for household in households
    ]


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
        "Use Household setup and Site setup to create the first "
        "records for your plant collection."
    )


def render_household_setup() -> None:
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
        load_household_options.clear()
        st.success(
            f"Created {result.household.name!r} with "
            f"{result.user.display_name!r} as the owner."
        )
        st.write(
            "Next, use Site setup to add a house, apartment, "
            "office, or greenhouse."
        )


def render_site_setup() -> None:
    """Display location search and site creation controls."""

    st.subheader("Create a site")
    st.write(
        "A site is a house, apartment, office, or greenhouse where "
        "plants live."
    )
    st.caption(
        "Search using a city or postal code. You do not need to provide "
        "an exact street address or floor plan."
    )

    households = load_household_options()

    if not households:
        st.warning("Create a household before adding a site.")
        return

    location_query = st.text_input(
        "City or postal code",
        placeholder="Example: Shrewsbury, Massachusetts",
        key="site_location_query",
    )

    if st.button(
        "Search locations",
        key="search_site_locations",
    ):
        try:
            results = get_geocoder().search(location_query)
        except GeocodingError as error:
            st.error(str(error))
        else:
            st.session_state["site_location_results"] = results

            if not results:
                st.warning(
                    "No matching locations were found. Try adding a "
                    "state, province, or country."
                )

    location_results: list[GeocodingResult] = st.session_state.get(
        "site_location_results",
        [],
    )

    if not location_results:
        st.info(
            "Search for an approximate location before completing "
            "the site form."
        )
        return

    selected_location = st.selectbox(
        "Choose the matching location",
        options=location_results,
        format_func=lambda result: result.display_name,
    )

    st.caption(
        "The selected result supplies approximate coordinates, elevation, "
        "and timezone for weather calculations."
    )

    site_types = list(SiteType)
    terrain_positions = list(TerrainPosition)

    with st.form("site_setup_form"):
        household = st.selectbox(
            "Household",
            options=households,
            format_func=lambda option: option.name,
        )
        site_name = st.text_input(
            "Site name",
            placeholder="Shrewsbury Home",
        )
        site_type = st.selectbox(
            "Site type",
            options=site_types,
            format_func=lambda value: value.value.replace("_", " ").title(),
        )
        terrain_position = st.selectbox(
            "Terrain position",
            options=terrain_positions,
            index=terrain_positions.index(TerrainPosition.UNKNOWN),
            format_func=lambda value: value.value.replace("_", " ").title(),
            help=(
                "A broad description is enough. Exact topographic "
                "measurements are not required."
            ),
        )
        weather_enabled = st.checkbox(
            "Enable weather tracking",
            value=True,
        )
        weather_sync_interval_minutes = st.number_input(
            "Weather update interval in minutes",
            min_value=15,
            max_value=1440,
            value=60,
            step=15,
        )
        submitted = st.form_submit_button(
            "Create site",
            type="primary",
        )

    if not submitted:
        return

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            site = create_site(
                session,
                household_id=household.id,
                name=site_name,
                site_type=site_type,
                timezone=selected_location.timezone,
                address_text=selected_location.display_name,
                latitude=selected_location.latitude,
                longitude=selected_location.longitude,
                elevation_m=selected_location.elevation_m,
                terrain_position=terrain_position,
                weather_enabled=weather_enabled,
                weather_sync_interval_minutes=int(
                    weather_sync_interval_minutes
                ),
            )
    except SiteSetupError as error:
        st.error(str(error))
    except SQLAlchemyError:
        st.error(
            "The site could not be saved. Confirm that the "
            "database migrations are current."
        )
    else:
        st.success(
            f"Created site {site.name!r} using the approximate location "
            f"{selected_location.display_name!r}."
        )
        st.write(
            "The next step is adding rooms or other spaces within this site."
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

dashboard_tab, household_tab, site_tab = st.tabs(
    [
        "Dashboard",
        "Household setup",
        "Site setup",
    ]
)

with dashboard_tab:
    render_dashboard()

with household_tab:
    render_household_setup()

with site_tab:
    render_site_setup()