"""Streamlit view for browsing the saved plant collection."""

from __future__ import annotations

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from plant_health.services import (
    PlantCollectionItem,
    load_plant_collection,
)


def _plant_matches_search(
    plant: PlantCollectionItem,
    search_text: str,
) -> bool:
    """Return whether a plant matches the collection search."""

    if not search_text:
        return True

    searchable_values = [
        plant.nickname,
        plant.plant_code,
        plant.common_name,
        plant.scientific_name,
        plant.household_name,
        plant.site_name,
        plant.space_name,
        plant.zone_name,
    ]
    searchable_text = " ".join(
        value for value in searchable_values if value
    ).casefold()

    return search_text.casefold() in searchable_text


def _format_status(status_value: str) -> str:
    """Convert a stored status value into a readable label."""

    return status_value.replace("_", " ").title()


def _render_plant_card(plant: PlantCollectionItem) -> None:
    """Display one plant and its current location."""

    display_name = plant.nickname or plant.plant_code
    species_name = (
        plant.common_name
        or plant.scientific_name
        or "Species not identified"
    )
    location_parts = [
        plant.site_name,
        plant.space_name,
        plant.zone_name,
    ]
    location = " — ".join(
        part for part in location_parts if part
    )

    if not location:
        location = "No current location"

    with st.container(border=True):
        name_column, status_column = st.columns([3, 1])

        with name_column:
            st.subheader(f"🌱 {display_name}")
            st.caption(f"Plant code: {plant.plant_code}")

        with status_column:
            st.write(
                f"**{_format_status(plant.status.value)}**"
            )

        household_column, species_column, location_column = st.columns(3)

        with household_column:
            st.caption("Household")
            st.write(plant.household_name)

        with species_column:
            st.caption("Species")
            st.write(species_name)

            if (
                plant.scientific_name
                and plant.scientific_name != species_name
            ):
                st.caption(plant.scientific_name)

        with location_column:
            st.caption("Current location")
            st.write(location)

        if plant.acquired_on is not None:
            st.caption(
                "Acquired "
                f"{plant.acquired_on.strftime('%B %d, %Y')}"
            )


def render_plant_collection(
    session_factory: sessionmaker,
) -> None:
    """Display searchable and filterable saved plants."""

    st.subheader("Plant collection")
    st.write(
        "Browse the individual plants saved by your households and see "
        "where each plant is currently located."
    )

    try:
        with session_factory() as session:
            collection = load_plant_collection(session)
    except SQLAlchemyError:
        st.error(
            "The plant collection could not be loaded. Confirm that the "
            "database migrations are current."
        )
        return

    if not collection:
        st.info(
            "No plants have been added yet. Use the Add plant tab to "
            "create your first plant."
        )
        return

    household_names = sorted(
        {plant.household_name for plant in collection}
    )
    status_values = sorted(
        {plant.status.value for plant in collection}
    )

    search_column, household_column, status_column = st.columns(3)

    with search_column:
        search_text = st.text_input(
            "Search plants",
            placeholder="Search by name, species, code, or location",
        )

    with household_column:
        selected_household = st.selectbox(
            "Household",
            options=["All households", *household_names],
        )

    with status_column:
        selected_status = st.selectbox(
            "Status",
            options=["All statuses", *status_values],
            format_func=lambda value: (
                value
                if value == "All statuses"
                else _format_status(value)
            ),
        )

    filtered_collection = [
        plant
        for plant in collection
        if _plant_matches_search(plant, search_text)
        and (
            selected_household == "All households"
            or plant.household_name == selected_household
        )
        and (
            selected_status == "All statuses"
            or plant.status.value == selected_status
        )
    ]

    st.caption(
        f"Showing {len(filtered_collection)} of "
        f"{len(collection)} plants."
    )

    if not filtered_collection:
        st.warning(
            "No plants match the current search and filters."
        )
        return

    for plant in filtered_collection:
        _render_plant_card(plant)