"""Services for recording plant care events."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    CareEvent,
    CareEventSource,
    CareEventType,
    HouseholdMembership,
    Plant,
)
from plant_health.database.models.common import utc_now


class CareRecordingError(ValueError):
    """Raised when a care event cannot be recorded."""


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values."""

    if value is None:
        return None

    cleaned_value = value.strip()
    return cleaned_value or None


def _as_utc(value: datetime) -> datetime:
    """Return a timezone-aware UTC value for safe comparisons."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def record_care_event(
    session: Session,
    *,
    household_id: UUID,
    plant_id: UUID,
    event_type: CareEventType,
    occurred_at: datetime | None = None,
    performed_by_user_id: UUID | None = None,
    source: CareEventSource = CareEventSource.MANUAL,
    amount_ml: Decimal | None = None,
    fertilizer_name: str | None = None,
    fertilizer_dilution_ratio: Decimal | None = None,
    water_ph: Decimal | None = None,
    water_ec_ms_cm: Decimal | None = None,
    product_name: str | None = None,
    notes: str | None = None,
) -> CareEvent:
    """Record a care event performed for one plant."""

    plant = session.get(Plant, plant_id)

    if plant is None or plant.household_id != household_id:
        raise CareRecordingError(
            "The selected plant does not belong to this household."
        )

    if performed_by_user_id is not None:
        membership = session.scalars(
            select(HouseholdMembership).where(
                HouseholdMembership.household_id == household_id,
                HouseholdMembership.user_id == performed_by_user_id,
                HouseholdMembership.ended_at.is_(None),
            )
        ).first()

        if membership is None:
            raise CareRecordingError(
                "The selected person is not an active member of this "
                "household."
            )

    event_time = occurred_at or utc_now()

    if _as_utc(event_time) > _as_utc(utc_now()):
        raise CareRecordingError(
            "The care event time cannot be in the future."
        )

    if amount_ml is not None and amount_ml < 0:
        raise CareRecordingError("Amount must be zero or greater.")

    if water_ph is not None and not (
        Decimal(0) <= water_ph <= Decimal(14)
    ):
        raise CareRecordingError("Water pH must be between 0 and 14.")

    if water_ec_ms_cm is not None and water_ec_ms_cm < 0:
        raise CareRecordingError("Water EC must be zero or greater.")

    if (
        fertilizer_dilution_ratio is not None
        and fertilizer_dilution_ratio <= 0
    ):
        raise CareRecordingError(
            "Fertilizer dilution ratio must be greater than zero."
        )

    clean_fertilizer_name = _optional_text(fertilizer_name)
    clean_product_name = _optional_text(product_name)
    clean_notes = _optional_text(notes)

    care_event = CareEvent(
        plant_id=plant.id,
        performed_by_user_id=performed_by_user_id,
        occurred_at=event_time,
        event_type=event_type,
        source=source,
        amount_ml=amount_ml,
        fertilizer_name=clean_fertilizer_name,
        fertilizer_dilution_ratio=fertilizer_dilution_ratio,
        water_ph=water_ph,
        water_ec_ms_cm=water_ec_ms_cm,
        product_name=clean_product_name,
        notes=clean_notes,
    )

    try:
        session.add(care_event)
        session.commit()
        session.refresh(care_event)
    except IntegrityError as error:
        session.rollback()
        raise CareRecordingError(
            "The care event could not be saved."
        ) from error
    except Exception:
        session.rollback()
        raise

    return care_event
