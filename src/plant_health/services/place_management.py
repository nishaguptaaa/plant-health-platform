"""Services for renaming and deactivating saved places."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    Site,
    Space,
)


class PlaceManagementError(ValueError):
    """Raised when a saved place cannot be updated."""


def _clean_name(value: str) -> str:
    """Remove surrounding whitespace and reject an empty name."""

    cleaned_value = value.strip()

    if not cleaned_value:
        raise PlaceManagementError("Name is required.")

    return cleaned_value


def _save_record[
    PlaceRecord: (
        Household,
        Site,
        Space,
        EnvironmentalZone,
    )
](
    session: Session,
    record: PlaceRecord,
    *,
    error_message: str,
) -> PlaceRecord:
    """Commit and refresh an updated database record."""

    try:
        session.commit()
        session.refresh(record)
    except IntegrityError as error:
        session.rollback()
        raise PlaceManagementError(error_message) from error
    except Exception:
        session.rollback()
        raise

    return record


def rename_household(
    session: Session,
    *,
    household_id: UUID,
    new_name: str,
) -> Household:
    """Rename an existing household."""

    household = session.get(Household, household_id)

    if household is None:
        raise PlaceManagementError("The selected household does not exist.")

    household.name = _clean_name(new_name)

    return _save_record(
        session,
        household,
        error_message="The household could not be renamed.",
    )


def rename_site(
    session: Session,
    *,
    site_id: UUID,
    new_name: str,
) -> Site:
    """Rename an existing site."""

    site = session.get(Site, site_id)

    if site is None:
        raise PlaceManagementError("The selected site does not exist.")

    clean_name = _clean_name(new_name)

    existing_site = session.scalar(
        select(Site).where(
            Site.household_id == site.household_id,
            Site.name == clean_name,
            Site.id != site.id,
        )
    )

    if existing_site is not None:
        raise PlaceManagementError(
            "A site with this name already exists in the household."
        )

    site.name = clean_name

    return _save_record(
        session,
        site,
        error_message="The site could not be renamed.",
    )


def rename_space(
    session: Session,
    *,
    space_id: UUID,
    new_name: str,
) -> Space:
    """Rename an existing room or growing space."""

    space = session.get(Space, space_id)

    if space is None:
        raise PlaceManagementError("The selected space does not exist.")

    clean_name = _clean_name(new_name)

    existing_space = session.scalar(
        select(Space).where(
            Space.site_id == space.site_id,
            Space.parent_space_id == space.parent_space_id,
            Space.name == clean_name,
            Space.id != space.id,
        )
    )

    if existing_space is not None:
        raise PlaceManagementError(
            "A space with this name already exists at this level."
        )

    space.name = clean_name

    return _save_record(
        session,
        space,
        error_message="The space could not be renamed.",
    )


def rename_zone(
    session: Session,
    *,
    zone_id: UUID,
    new_name: str,
) -> EnvironmentalZone:
    """Rename an existing plant-placement zone."""

    zone = session.get(EnvironmentalZone, zone_id)

    if zone is None:
        raise PlaceManagementError("The selected zone does not exist.")

    clean_name = _clean_name(new_name)

    existing_zone = session.scalar(
        select(EnvironmentalZone).where(
            EnvironmentalZone.space_id == zone.space_id,
            EnvironmentalZone.name == clean_name,
            EnvironmentalZone.id != zone.id,
        )
    )

    if existing_zone is not None:
        raise PlaceManagementError(
            "A zone with this name already exists in the selected space."
        )

    zone.name = clean_name

    return _save_record(
        session,
        zone,
        error_message="The zone could not be renamed.",
    )


def deactivate_site(
    session: Session,
    *,
    site_id: UUID,
) -> Site:
    """Hide a site without deleting its history."""

    site = session.get(Site, site_id)

    if site is None:
        raise PlaceManagementError("The selected site does not exist.")

    site.active = False

    return _save_record(
        session,
        site,
        error_message="The site could not be deactivated.",
    )


def deactivate_space(
    session: Session,
    *,
    space_id: UUID,
) -> Space:
    """Hide a space without deleting its history."""

    space = session.get(Space, space_id)

    if space is None:
        raise PlaceManagementError("The selected space does not exist.")

    space.active = False

    return _save_record(
        session,
        space,
        error_message="The space could not be deactivated.",
    )


def deactivate_zone(
    session: Session,
    *,
    zone_id: UUID,
) -> EnvironmentalZone:
    """Hide a zone without deleting its history."""

    zone = session.get(EnvironmentalZone, zone_id)

    if zone is None:
        raise PlaceManagementError("The selected zone does not exist.")

    zone.active = False

    return _save_record(
        session,
        zone,
        error_message="The zone could not be deactivated.",
    )