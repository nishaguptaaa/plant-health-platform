"""Streamlit controls for moving plants between zones."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from plant_health.database.models import LocationChangeReason
from plant_health.services import (
    HouseholdPlaces,
    PlantCollectionItem,
    PlantMovementError,
    move_plant,
)


@dataclass(frozen=True, slots=True)
class MovementDestination:
    """One environmental zone available as a movement destination."""

    household_id: UUID
    zone_id: UUID
    label: str


def _format_enum_value(value: str) -> str:
    """Convert a stored enum value into a readable label."""

    return value.replace("_", " ").title()


def _plant_option_label(plant: PlantCollectionItem) -> str:
    """Create a recognizable label for a plant."""

    plant_name = plant.nickname or plant.plant_code
    return (
        f"{plant_name} — {plant.household_name} — "
        f"{plant.plant_code}"
    )


def _load_destinations(
    places: list[HouseholdPlaces],
    *,
    household_id: UUID,
    current_zone_id: UUID | None,
) -> list[MovementDestination]:
    """Load active zones in the plant's household except its current zone."""

    destinations: list[MovementDestination] = []

    for household in places:
        if household.id != household_id:
            continue

        for site in household.sites:
            for space in site.spaces:
                for zone in space.zones:
                    if zone.id == current_zone_id:
                        continue

                    destinations.append(
                        MovementDestination(
                            household_id=household.id,
                            zone_id=zone.id,
                            label=(
                                f"{site.name} — "
                                f"{space.name} — "
                                f"{zone.name}"
                            ),
                        )
                    )

    return destinations


def render_plant_movement(
    session_factory: sessionmaker,
    *,
    collection: list[PlantCollectionItem],
    places: list[HouseholdPlaces],
) -> None:
    """Display controls for moving a plant to another zone."""

    message = st.session_state.pop(
        "plant_movement_message",
        None,
    )

    if message is not None:
        st.success(message)

    st.subheader("Move a plant")
    st.write(
        "Assign a plant to a new plant-placement zone while preserving "
        "its previous location in the plant's history."
    )

    if not collection:
        st.info(
            "No plants are available to move. Add a plant first."
        )
        return

    selected_plant = st.selectbox(
        "Choose a plant to move",
        options=collection,
        format_func=_plant_option_label,
        key="plant_movement_selection",
    )

    current_location_parts = [
        selected_plant.site_name,
        selected_plant.space_name,
        selected_plant.zone_name,
    ]
    current_location = " — ".join(
        part for part in current_location_parts if part
    )

    st.caption("Current location")
    st.write(current_location or "No current location")

    destinations = _load_destinations(
        places,
        household_id=selected_plant.household_id,
        current_zone_id=selected_plant.zone_id,
    )

    if not destinations:
        st.warning(
            "This household has no other active zones available. "
            "Create another plant-placement zone before moving this plant."
        )
        return

    destination = st.selectbox(
        "Move this plant to",
        options=destinations,
        format_func=lambda option: option.label,
        key=f"plant_destination_{selected_plant.id}",
    )

    movement_reasons = [
        reason
        for reason in LocationChangeReason
        if reason != LocationChangeReason.INITIAL_PLACEMENT
    ]

    with st.form(
        f"plant_movement_form_{selected_plant.id}"
    ):
        reason = st.selectbox(
            "Why are you moving this plant?",
            options=movement_reasons,
            format_func=lambda option: _format_enum_value(
                option.value
            ),
        )
        placement_label = st.text_input(
            "Exact position in the new zone (optional)",
            placeholder="Example: Right side of the middle shelf",
        )
        notes = st.text_area(
            "Movement notes (optional)",
            placeholder=(
                "Example: Moving away from strong afternoon sunlight."
            ),
        )
        submitted = st.form_submit_button(
            "Move plant",
            type="primary",
        )

    if not submitted:
        return

    try:
        with session_factory() as session:
            result = move_plant(
                session,
                household_id=selected_plant.household_id,
                plant_id=selected_plant.id,
                new_zone_id=destination.zone_id,
                reason=reason,
                placement_label=placement_label,
                notes=notes,
            )
    except PlantMovementError as error:
        st.error(str(error))
        return
    except SQLAlchemyError:
        st.error(
            "The plant movement could not be saved. Confirm that the "
            "database migrations are current."
        )
        return

    plant_name = result.plant.nickname or result.plant.plant_code

    st.session_state["plant_movement_message"] = (
        f"Moved {plant_name!r} to {destination.label!r}."
    )
    st.cache_data.clear()
    st.rerun()