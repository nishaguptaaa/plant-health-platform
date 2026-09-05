"""Streamlit controls for adding individual plants."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from plant_health.services import (
    HouseholdPlaces,
    PlantSetupError,
    create_plant_with_location,
)


@dataclass(frozen=True, slots=True)
class PlantPlacementOption:
    """A household and zone available for an initial plant placement."""

    household_id: UUID
    zone_id: UUID
    label: str


def _load_placement_options(
    places: list[HouseholdPlaces],
) -> list[PlantPlacementOption]:
    """Flatten active zones into plant-placement options."""

    options: list[PlantPlacementOption] = []

    for household in places:
        for site in household.sites:
            for space in site.spaces:
                for zone in space.zones:
                    options.append(
                        PlantPlacementOption(
                            household_id=household.id,
                            zone_id=zone.id,
                            label=(
                                f"{household.name} — "
                                f"{site.name} — "
                                f"{space.name} — "
                                f"{zone.name}"
                            ),
                        )
                    )

    return options


def render_plant_setup(
    session_factory: sessionmaker,
    *,
    places: list[HouseholdPlaces],
) -> None:
    """Display controls for adding a plant and its initial location."""

    message = st.session_state.pop(
        "plant_setup_message",
        None,
    )

    if message is not None:
        st.success(message)

    st.subheader("Add a plant")
    st.write(
        "Create an individual plant record and assign its first "
        "plant-placement zone."
    )
    st.caption(
        "You can add species identification, container details, growing "
        "method, and care history in later steps."
    )

    placement_options = _load_placement_options(places)

    if not placement_options:
        st.warning(
            "Create at least one active plant-placement zone before "
            "adding a plant."
        )
        return

    selected_placement = st.selectbox(
        "Where is this plant currently located?",
        options=placement_options,
        format_func=lambda option: option.label,
        key="new_plant_placement",
    )

    with st.form("plant_setup_form"):
        nickname = st.text_input(
            "Plant name or nickname",
            placeholder="Kitchen Orchid",
            help=(
                "Use any name that helps your household recognize this "
                "individual plant."
            ),
        )
        acquired_on = st.date_input(
            "When did you get this plant? (optional)",
            value=None,
            max_value=datetime.now(UTC).date(),
        )
        acquisition_source = st.text_input(
            "Where did you get it? (optional)",
            placeholder="Local nursery, gift, propagation, or online store",
        )
        placement_label = st.text_input(
            "Exact position within the zone (optional)",
            placeholder="Left side of the top shelf",
            help=(
                "This is useful when several plants share the same shelf, "
                "table, or windowsill."
            ),
        )
        notes = st.text_area(
            "Initial notes (optional)",
            placeholder=(
                "Example: Arrived in a clear nursery pot with care "
                "instructions attached."
            ),
        )
        submitted = st.form_submit_button(
            "Add plant",
            type="primary",
        )

    if not submitted:
        return

    try:
        with session_factory() as session:
            result = create_plant_with_location(
                session,
                household_id=selected_placement.household_id,
                zone_id=selected_placement.zone_id,
                nickname=nickname,
                acquired_on=acquired_on,
                acquisition_source=acquisition_source,
                placement_label=placement_label,
                notes=notes,
            )
    except PlantSetupError as error:
        st.error(str(error))
        return
    except SQLAlchemyError:
        st.error(
            "The plant could not be saved. Confirm that the "
            "database migrations are current."
        )
        return

    st.session_state["plant_setup_message"] = (
        f"Added {result.plant.nickname!r} with plant code "
        f"{result.plant.plant_code}."
    )
    st.cache_data.clear()
    st.rerun()