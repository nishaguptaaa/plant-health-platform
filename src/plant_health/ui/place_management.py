"""Streamlit controls for renaming and deactivating saved places."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from plant_health.services import (
    HouseholdPlaces,
    PlaceManagementError,
    deactivate_site,
    deactivate_space,
    deactivate_zone,
    rename_household,
    rename_site,
    rename_space,
    rename_zone,
)


@dataclass(frozen=True, slots=True)
class PlaceOption:
    """One saved record that can be managed."""

    id: UUID
    name: str
    label: str


def _load_management_options(
    places: list[HouseholdPlaces],
    *,
    record_type: str,
) -> list[PlaceOption]:
    """Flatten the selected kind of place into display options."""

    options: list[PlaceOption] = []

    for household in places:
        if record_type == "Household":
            options.append(
                PlaceOption(
                    id=household.id,
                    name=household.name,
                    label=household.name,
                )
            )
            continue

        for site in household.sites:
            if record_type == "Site":
                options.append(
                    PlaceOption(
                        id=site.id,
                        name=site.name,
                        label=f"{household.name} — {site.name}",
                    )
                )
                continue

            for space in site.spaces:
                if record_type == "Space":
                    options.append(
                        PlaceOption(
                            id=space.id,
                            name=space.name,
                            label=(
                                f"{household.name} — "
                                f"{site.name} — {space.name}"
                            ),
                        )
                    )
                    continue

                for zone in space.zones:
                    if record_type == "Zone":
                        options.append(
                            PlaceOption(
                                id=zone.id,
                                name=zone.name,
                                label=(
                                    f"{household.name} — "
                                    f"{site.name} — "
                                    f"{space.name} — "
                                    f"{zone.name}"
                                ),
                            )
                        )

    return options


def _rename_selected_record(
    session_factory: sessionmaker,
    *,
    record_type: str,
    record_id: UUID,
    new_name: str,
) -> str:
    """Rename the selected record and return a confirmation message."""

    with session_factory() as session:
        if record_type == "Household":
            record = rename_household(
                session,
                household_id=record_id,
                new_name=new_name,
            )
        elif record_type == "Site":
            record = rename_site(
                session,
                site_id=record_id,
                new_name=new_name,
            )
        elif record_type == "Space":
            record = rename_space(
                session,
                space_id=record_id,
                new_name=new_name,
            )
        else:
            record = rename_zone(
                session,
                zone_id=record_id,
                new_name=new_name,
            )

    return f"Renamed {record_type.lower()} to {record.name!r}."


def _deactivate_selected_record(
    session_factory: sessionmaker,
    *,
    record_type: str,
    record_id: UUID,
    record_name: str,
) -> str:
    """Deactivate the selected site, space, or zone."""

    with session_factory() as session:
        if record_type == "Site":
            deactivate_site(
                session,
                site_id=record_id,
            )
        elif record_type == "Space":
            deactivate_space(
                session,
                space_id=record_id,
            )
        else:
            deactivate_zone(
                session,
                zone_id=record_id,
            )

    return (
        f"Deactivated {record_type.lower()} {record_name!r}. "
        "Its database history was not deleted."
    )


def render_place_management(
    session_factory: sessionmaker,
    *,
    places: list[HouseholdPlaces],
) -> None:
    """Display controls for renaming and deactivating places."""

    message = st.session_state.pop(
        "place_management_message",
        None,
    )

    if message is not None:
        st.success(message)

    st.write(
        "Rename saved records or hide sites, spaces, and zones that "
        "are no longer active."
    )
    st.caption(
        "Deactivation is reversible at the database level and does not "
        "delete historical records."
    )

    record_type = st.selectbox(
        "What would you like to manage?",
        options=[
            "Household",
            "Site",
            "Space",
            "Zone",
        ],
        key="managed_record_type",
    )

    options = _load_management_options(
        places,
        record_type=record_type,
    )

    if not options:
        st.info(
            f"No active {record_type.lower()} records are available."
        )
        return

    selected_record = st.selectbox(
        f"Choose a {record_type.lower()}",
        options=options,
        format_func=lambda option: option.label,
        key="managed_record",
    )

    can_deactivate = record_type != "Household"

    with st.form(
        f"manage_{record_type.lower()}_form",
    ):
        new_name = st.text_input(
            "Name",
            value=selected_record.name,
        )

        if can_deactivate:
            confirm_deactivation = st.checkbox(
                "I understand that this record will be hidden from "
                "the active Places views."
            )
        else:
            confirm_deactivation = False

        rename_column, deactivate_column = st.columns(2)

        with rename_column:
            rename_submitted = st.form_submit_button(
                "Save new name",
                type="primary",
            )

        with deactivate_column:
            if can_deactivate:
                deactivate_submitted = st.form_submit_button(
                    "Deactivate",
                )
            else:
                deactivate_submitted = False

    if not rename_submitted and not deactivate_submitted:
        return

    if deactivate_submitted and not confirm_deactivation:
        st.error(
            "Confirm that you understand the record will be hidden "
            "before deactivating it."
        )
        return

    try:
        if rename_submitted:
            confirmation_message = _rename_selected_record(
                session_factory,
                record_type=record_type,
                record_id=selected_record.id,
                new_name=new_name,
            )
        else:
            confirmation_message = _deactivate_selected_record(
                session_factory,
                record_type=record_type,
                record_id=selected_record.id,
                record_name=selected_record.name,
            )
    except PlaceManagementError as error:
        st.error(str(error))
        return
    except SQLAlchemyError:
        st.error(
            "The record could not be updated. Confirm that the "
            "database migrations are current."
        )
        return

    st.session_state["place_management_message"] = confirmation_message
    st.cache_data.clear()
    st.rerun()