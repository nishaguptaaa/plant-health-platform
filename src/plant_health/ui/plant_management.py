"""Streamlit controls for editing existing plants."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from plant_health.database.models import (
    IdentificationStatus,
    PlantStatus,
)
from plant_health.services import (
    PlantCollectionItem,
    PlantManagementError,
    update_plant_details,
)


def _format_enum_value(value: str) -> str:
    """Convert a stored enum value into a readable label."""

    return value.replace("_", " ").title()


def _plant_option_label(plant: PlantCollectionItem) -> str:
    """Create a recognizable plant-selection label."""

    plant_name = plant.nickname or plant.plant_code
    return (
        f"{plant_name} — {plant.household_name} — "
        f"{plant.plant_code}"
    )


def render_plant_management(
    session_factory: sessionmaker,
    *,
    collection: list[PlantCollectionItem],
) -> None:
    """Display controls for editing a saved plant."""

    message = st.session_state.pop(
        "plant_management_message",
        None,
    )

    if message is not None:
        st.success(message)

    st.subheader("Edit a plant")
    st.write(
        "Update a plant's name, status, identification, acquisition "
        "information, and notes."
    )
    st.caption(
        "Editing these details does not erase the plant's location, care, "
        "observation, or health history."
    )

    if not collection:
        st.info(
            "No plants are available to edit. Add a plant first."
        )
        return

    selected_plant = st.selectbox(
        "Choose a plant to edit",
        options=collection,
        format_func=_plant_option_label,
        key="plant_management_selection",
    )

    statuses = list(PlantStatus)
    identification_statuses = list(IdentificationStatus)

    with st.form(
        f"plant_management_form_{selected_plant.id}"
    ):
        st.markdown("#### Basic details")

        nickname = st.text_input(
            "Plant name or nickname",
            value=selected_plant.nickname or "",
        )
        status = st.selectbox(
            "Plant status",
            options=statuses,
            index=statuses.index(selected_plant.status),
            format_func=lambda option: _format_enum_value(
                option.value
            ),
        )
        cultivar_name = st.text_input(
            "Cultivar or variety (optional)",
            value=selected_plant.cultivar_name or "",
            placeholder="Example: Marble Queen",
        )

        st.markdown("#### Species identification")
        st.caption(
            "If you know the species, enter its scientific name. "
            "Otherwise, leave this section blank."
        )

        scientific_name = st.text_input(
            "Scientific name (optional)",
            value=selected_plant.scientific_name or "",
            placeholder="Example: Epipremnum aureum",
        )
        common_name = st.text_input(
            "Common name (optional)",
            value=selected_plant.common_name or "",
            placeholder="Example: Golden Pothos",
            help=(
                "A scientific name is required before a common name "
                "can be saved as a species identification."
            ),
        )
        identification_status = st.selectbox(
            "Identification status",
            options=identification_statuses,
            index=identification_statuses.index(
                selected_plant.identification_status
            ),
            format_func=lambda option: _format_enum_value(
                option.value
            ),
        )
        identification_confidence = st.number_input(
            "Identification confidence from 0 to 1 (optional)",
            min_value=0.0,
            max_value=1.0,
            value=(
                None
                if selected_plant.identification_confidence is None
                else float(
                    selected_plant.identification_confidence
                )
            ),
            step=0.05,
            format="%.2f",
            help=(
                "Use this mainly for AI-suggested identifications. "
                "For example, 0.85 means 85% confidence."
            ),
        )

        st.markdown("#### Acquisition and lifecycle")

        acquired_on = st.date_input(
            "When did you get this plant? (optional)",
            value=selected_plant.acquired_on,
            max_value=datetime.now(UTC).date(),
        )
        acquisition_source = st.text_input(
            "Where did you get it? (optional)",
            value=selected_plant.acquisition_source or "",
            placeholder="Local nursery, gift, propagation, or online store",
        )
        deceased_on = st.date_input(
            "Date the plant died (optional)",
            value=selected_plant.deceased_on,
            max_value=datetime.now(UTC).date(),
            help=(
                "Leave this blank unless the plant has died. "
                "You can also change its status to Deceased."
            ),
        )
        notes = st.text_area(
            "Plant notes (optional)",
            value=selected_plant.notes or "",
        )

        submitted = st.form_submit_button(
            "Save plant changes",
            type="primary",
        )

    if not submitted:
        return

    confidence = (
        None
        if identification_confidence is None
        else Decimal(str(identification_confidence))
    )

    try:
        with session_factory() as session:
            result = update_plant_details(
                session,
                household_id=selected_plant.household_id,
                plant_id=selected_plant.id,
                nickname=nickname,
                status=status,
                scientific_name=scientific_name,
                common_name=common_name,
                cultivar_name=cultivar_name,
                identification_status=identification_status,
                identification_confidence=confidence,
                acquired_on=acquired_on,
                acquisition_source=acquisition_source,
                deceased_on=deceased_on,
                notes=notes,
            )
    except PlantManagementError as error:
        st.error(str(error))
        return
    except SQLAlchemyError:
        st.error(
            "The plant changes could not be saved. Confirm that the "
            "database migrations are current."
        )
        return

    st.session_state["plant_management_message"] = (
        f"Saved changes to {result.plant.nickname!r}."
    )
    st.cache_data.clear()
    st.rerun()