"""Streamlit entry point for the Plant Health Platform."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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
    ObstructionLevel,
    Plant,
    Site,
    SiteType,
    Space,
    SpaceType,
    Task,
    TaskStatus,
    TerrainPosition,
    WeatherSnapshot,
    ZoneType,
)
from plant_health.services import (
    HouseholdPlaces,
    HouseholdSetupError,
    SiteSetupError,
    SpaceSetupError,
    ZoneSetupError,
    create_environmental_zone,
    create_household_with_owner,
    create_site,
    create_space,
    load_place_hierarchy,
)
from plant_health.ui import (
    render_place_management,
    render_plant_collection,
    render_plant_setup,
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


@dataclass(frozen=True, slots=True)
class SiteOption:
    """A site option displayed without exposing its database ID."""

    id: UUID
    name: str
    household_name: str


@dataclass(frozen=True, slots=True)
class SpaceOption:
    """A space option displayed without exposing its database ID."""

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


@st.cache_data(ttl=30)
def load_site_options() -> list[SiteOption]:
    """Load active sites for application selection controls."""

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            rows = session.execute(
                select(
                    Site.id,
                    Site.name,
                    Household.name.label("household_name"),
                )
                .join(
                    Household,
                    Site.household_id == Household.id,
                )
                .where(Site.active.is_(True))
                .order_by(Household.name, Site.name)
            ).all()
    except SQLAlchemyError:
        return []

    return [
        SiteOption(
            id=row.id,
            name=row.name,
            household_name=row.household_name,
        )
        for row in rows
    ]


@st.cache_data(ttl=30)
def load_space_options(site_id: UUID) -> list[SpaceOption]:
    """Load active spaces belonging to one site."""

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            rows = session.execute(
                select(
                    Space.id,
                    Space.name,
                )
                .where(
                    Space.site_id == site_id,
                    Space.active.is_(True),
                )
                .order_by(Space.name)
            ).all()
    except SQLAlchemyError:
        return []

    return [
        SpaceOption(
            id=row.id,
            name=row.name,
        )
        for row in rows
    ]


@st.cache_data(ttl=30)
def load_places() -> list[HouseholdPlaces]:
    """Load the complete local household place hierarchy."""

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            return load_place_hierarchy(session)
    except SQLAlchemyError:
        return []


def display_enum_value(value: object) -> str:
    """Convert a string enum value into a readable label."""

    raw_value = getattr(value, "value", str(value))
    return str(raw_value).replace("_", " ").title()


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
        "Use Places to review your location hierarchy or use the setup "
        "tabs to add new records."
    )


def render_places() -> None:
    """Display hierarchy, list, and future map views of saved places."""

    st.subheader("Places")
    st.write(
        "Review how your households, sites, rooms, and plant-placement "
        "zones are organized."
    )

    places = load_places()

    if not places:
        st.info(
            "No saved places are available yet. Start by creating a "
            "household and site."
        )
        return

    hierarchy_tab, list_tab, map_tab, manage_tab = st.tabs(
        [
            "Hierarchy",
            "List",
            "Map",
            "Manage",
        ]
    )

    with hierarchy_tab:
        for household in places:
            st.markdown(f"### 🏠 {household.name}")

            if not household.sites:
                st.caption("No sites have been added to this household.")
                continue

            for site in household.sites:
                with st.container(border=True):
                    st.markdown(f"#### 📍 {site.name}")
                    st.caption(
                        f"Site type: {display_enum_value(site.site_type)}"
                    )

                    if not site.spaces:
                        st.write("No rooms or growing spaces added yet.")
                        continue

                    space_names = {
                        space.id: space.name
                        for space in site.spaces
                    }

                    for space in site.spaces:
                        st.markdown(
                            f"**🚪 {space.name}** "
                            f"— {display_enum_value(space.space_type)}"
                        )

                        if space.parent_space_id is not None:
                            parent_name = space_names.get(
                                space.parent_space_id,
                                "Another space",
                            )
                            st.caption(f"Located inside: {parent_name}")

                        if not space.zones:
                            st.caption(
                                "No plant-placement zones added yet."
                            )
                            continue

                        for zone in space.zones:
                            st.markdown(
                                f"- 🌿 **{zone.name}** "
                                f"({display_enum_value(zone.zone_type)})"
                            )

    with list_tab:
        rows: list[dict[str, str]] = []

        for household in places:
            if not household.sites:
                rows.append(
                    {
                        "Household": household.name,
                        "Site": "",
                        "Site type": "",
                        "Space": "",
                        "Space type": "",
                        "Zone": "",
                        "Zone type": "",
                    }
                )
                continue

            for site in household.sites:
                if not site.spaces:
                    rows.append(
                        {
                            "Household": household.name,
                            "Site": site.name,
                            "Site type": display_enum_value(
                                site.site_type
                            ),
                            "Space": "",
                            "Space type": "",
                            "Zone": "",
                            "Zone type": "",
                        }
                    )
                    continue

                for space in site.spaces:
                    if not space.zones:
                        rows.append(
                            {
                                "Household": household.name,
                                "Site": site.name,
                                "Site type": display_enum_value(
                                    site.site_type
                                ),
                                "Space": space.name,
                                "Space type": display_enum_value(
                                    space.space_type
                                ),
                                "Zone": "",
                                "Zone type": "",
                            }
                        )
                        continue

                    for zone in space.zones:
                        rows.append(
                            {
                                "Household": household.name,
                                "Site": site.name,
                                "Site type": display_enum_value(
                                    site.site_type
                                ),
                                "Space": space.name,
                                "Space type": display_enum_value(
                                    space.space_type
                                ),
                                "Zone": zone.name,
                                "Zone type": display_enum_value(
                                    zone.zone_type
                                ),
                            }
                        )

        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
        )

    with map_tab:
        st.info(
            "The optional map view will let you draw simple rooms and "
            "place zones and plant-count icons on a private local floor plan."
        )
        st.markdown(
            """
Planned map features:

- Manually draw simple room shapes
- Optionally upload your own floor-plan image
- Drag zones to approximate locations
- Display plant icons and plant counts
- Keep floor-plan information local and private
"""
        )

    with manage_tab:
        render_place_management(
            get_session_factory(),
            places=places,
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
        load_places.clear()

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
            format_func=display_enum_value,
        )
        terrain_position = st.selectbox(
            "Terrain position",
            options=terrain_positions,
            index=terrain_positions.index(TerrainPosition.UNKNOWN),
            format_func=display_enum_value,
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
        load_site_options.clear()
        load_places.clear()

        st.success(
            f"Created site {site.name!r} using the approximate location "
            f"{selected_location.display_name!r}."
        )
        st.write(
            "The next step is adding rooms or other spaces within this site."
        )


def render_space_setup() -> None:
    """Display controls for creating rooms and other growing spaces."""

    st.subheader("Create a space")
    st.write(
        "A space is a room or major growing area within one of your sites."
    )
    st.caption(
        "Basic information is enough. Building-position details are "
        "optional and can be updated later."
    )

    sites = load_site_options()

    if not sites:
        st.warning("Create a site before adding a space.")
        return

    selected_site = st.selectbox(
        "Site",
        options=sites,
        format_func=lambda option: (
            f"{option.household_name} — {option.name}"
        ),
        key="space_site",
    )

    existing_spaces = load_space_options(selected_site.id)
    parent_options: list[SpaceOption | None] = [
        None,
        *existing_spaces,
    ]
    space_types = list(SpaceType)

    with st.form("space_setup_form"):
        space_name = st.text_input(
            "Space name",
            placeholder="Living Room",
        )
        space_type = st.selectbox(
            "Space type",
            options=space_types,
            format_func=display_enum_value,
        )
        parent_space = st.selectbox(
            "Parent space (optional)",
            options=parent_options,
            format_func=lambda option: (
                "No parent space"
                if option is None
                else option.name
            ),
            help=(
                "Use this when creating a distinct growing area inside "
                "another space, such as a grow tent or large plant rack."
            ),
        )
        floor_number = st.number_input(
            "Which floor of the building is this space on? (optional)",
            value=None,
            step=1,
            help=(
                "Examples: basement = -1, ground floor = 0 or 1, "
                "second floor = 2. Use your local numbering convention."
            ),
        )

        with st.expander(
            "Building position details (optional)",
            expanded=False,
        ):
            st.caption(
                "These questions describe where the room is located in "
                "the building. They do not describe the height of a plant "
                "or shelf."
            )

            height_above_ground_m = st.number_input(
                "About how high is this room above the outdoor ground? "
                "(meters)",
                min_value=-20.0,
                max_value=1000.0,
                value=None,
                step=0.1,
                format="%.2f",
                help=(
                    "Examples: ground-floor room = about 0 meters; "
                    "second-floor room = about 3 meters; "
                    "20th-floor room = about 60 meters. "
                    "Leave blank if you do not know."
                ),
            )

            below_grade_fraction_pct = st.number_input(
                "How much of this room is underground? (%)",
                min_value=0.0,
                max_value=100.0,
                value=None,
                step=5.0,
                format="%.1f",
                help=(
                    "This is mainly for basements. Enter 50 for a room "
                    "that is approximately halfway underground or 100 "
                    "for a room that is fully underground. Leave blank "
                    "for a normal above-ground room."
                ),
            )

        notes = st.text_area(
            "Notes (optional)",
            placeholder=(
                "Example: Bright room with two windows and a plant shelf."
            ),
        )
        submitted = st.form_submit_button(
            "Create space",
            type="primary",
        )

    if not submitted:
        return

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            space = create_space(
                session,
                site_id=selected_site.id,
                parent_space_id=(
                    None
                    if parent_space is None
                    else parent_space.id
                ),
                name=space_name,
                space_type=space_type,
                floor_number=(
                    None
                    if floor_number is None
                    else int(floor_number)
                ),
                height_above_ground_m=(
                    None
                    if height_above_ground_m is None
                    else Decimal(str(height_above_ground_m))
                ),
                below_grade_fraction_pct=(
                    None
                    if below_grade_fraction_pct is None
                    else Decimal(str(below_grade_fraction_pct))
                ),
                notes=notes,
            )
    except SpaceSetupError as error:
        st.error(str(error))
    except SQLAlchemyError:
        st.error(
            "The space could not be saved. Confirm that the "
            "database migrations are current."
        )
    else:
        load_space_options.clear()
        load_places.clear()

        st.success(
            f"Created space {space.name!r} within site "
            f"{selected_site.name!r}."
        )
        st.write(
            "Next, add environmental zones representing the specific "
            "places where plants can sit."
        )


def render_zone_setup() -> None:
    """Display controls for creating plant-placement zones."""

    st.subheader("Create a plant-placement zone")
    st.write(
        "A zone is a specific place within a room where one or more "
        "plants can sit."
    )
    st.caption(
        "Examples include a windowsill, table, shelf, plant stand, "
        "floor position, hanging planter, or bench."
    )

    sites = load_site_options()

    if not sites:
        st.warning("Create a site and space before adding a zone.")
        return

    selected_site = st.selectbox(
        "Site",
        options=sites,
        format_func=lambda option: (
            f"{option.household_name} — {option.name}"
        ),
        key="zone_site",
    )

    spaces = load_space_options(selected_site.id)

    if not spaces:
        st.warning(
            "Create a space within the selected site before adding a zone."
        )
        return

    selected_space = st.selectbox(
        "Room or space",
        options=spaces,
        format_func=lambda option: option.name,
        key="zone_space",
    )

    zone_types = list(ZoneType)
    obstruction_levels = list(ObstructionLevel)

    with st.form("zone_setup_form"):
        zone_name = st.text_input(
            "Zone name",
            placeholder="Bookshelf Top Shelf",
        )
        zone_type = st.selectbox(
            "What kind of plant position is this?",
            options=zone_types,
            format_func=display_enum_value,
        )
        description = st.text_area(
            "Description (optional)",
            placeholder=(
                "Example: Top shelf beside the large south-facing window."
            ),
        )
        height_above_floor_m = st.number_input(
            "How high is this plant position above the room's floor? "
            "(meters, optional)",
            min_value=0.0,
            max_value=100.0,
            value=None,
            step=0.1,
            format="%.2f",
            help=(
                "This describes the shelf, table, stand, or hanging "
                "position—not the room's height above outdoor ground. "
                "Examples: floor = 0, table = 0.75, shelf = 1.5."
            ),
        )
        direct_sun_possible = st.selectbox(
            "Can direct sunlight reach this exact plant position?",
            options=[None, True, False],
            format_func=lambda value: (
                "Unknown"
                if value is None
                else "Yes"
                if value
                else "No"
            ),
            help=(
                "Choose Yes if a visible beam of direct sun can reach "
                "plants placed here during any part of the day."
            ),
        )
        obstruction_level = st.selectbox(
            "How obstructed is the view toward the windows or sky?",
            options=obstruction_levels,
            index=obstruction_levels.index(ObstructionLevel.UNKNOWN),
            format_func=display_enum_value,
            help=(
                "Consider walls, furniture, curtains, nearby buildings, "
                "trees, and other objects that may block light."
            ),
        )
        estimated_sky_view_pct = st.number_input(
            "Approximately how much open sky is visible from this "
            "position? (%, optional)",
            min_value=0.0,
            max_value=100.0,
            value=None,
            step=5.0,
            format="%.1f",
            help=(
                "A rough estimate is enough. Enter 0 if no sky is visible "
                "or 100 for a completely open view. Leave blank if unsure."
            ),
        )
        submitted = st.form_submit_button(
            "Create zone",
            type="primary",
        )

    if not submitted:
        return

    session_factory = get_session_factory()

    try:
        with session_factory() as session:
            zone = create_environmental_zone(
                session,
                space_id=selected_space.id,
                name=zone_name,
                zone_type=zone_type,
                description=description,
                height_above_floor_m=(
                    None
                    if height_above_floor_m is None
                    else Decimal(str(height_above_floor_m))
                ),
                direct_sun_possible=direct_sun_possible,
                obstruction_level=obstruction_level,
                estimated_sky_view_pct=(
                    None
                    if estimated_sky_view_pct is None
                    else Decimal(str(estimated_sky_view_pct))
                ),
            )
    except ZoneSetupError as error:
        st.error(str(error))
    except SQLAlchemyError:
        st.error(
            "The zone could not be saved. Confirm that the "
            "database migrations are current."
        )
    else:
        load_places.clear()

        st.success(
            f"Created zone {zone.name!r} inside "
            f"{selected_space.name!r}."
        )
        st.write(
            "You can create additional zones for every shelf, table, "
            "stand, windowsill, or other plant position in this space."
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

(
    dashboard_tab,
    places_tab,
    plants_tab,
    household_tab,
    site_tab,
    space_tab,
    zone_tab,
) = st.tabs(
    [
        "Dashboard",
        "Places",
        "Plants",
        "Household setup",
        "Site setup",
        "Space setup",
        "Zone setup",
    ]
)

with dashboard_tab:
    render_dashboard()

with places_tab:
    render_places()

with plants_tab:
    browse_plants_tab, add_plant_tab = st.tabs(
        [
            "Browse plants",
            "Add plant",
        ]
    )

    with browse_plants_tab:
        render_plant_collection(
            get_session_factory(),
        )

    with add_plant_tab:
        render_plant_setup(
            get_session_factory(),
            places=load_places(),
        )

with household_tab:
    render_household_setup()

with site_tab:
    render_site_setup()

with space_tab:
    render_space_setup()

with zone_tab:
    render_zone_setup()