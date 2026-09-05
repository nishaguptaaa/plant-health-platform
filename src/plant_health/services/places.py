"""Read services for displaying the household place hierarchy."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from plant_health.database.models import (
    EnvironmentalZone,
    Household,
    Site,
    SiteType,
    Space,
    SpaceType,
    ZoneType,
)


@dataclass(frozen=True, slots=True)
class ZonePlace:
    """A plant-placement zone shown in the Places view."""

    id: UUID
    name: str
    zone_type: ZoneType


@dataclass(frozen=True, slots=True)
class SpacePlace:
    """A room or growing space shown in the Places view."""

    id: UUID
    name: str
    space_type: SpaceType
    parent_space_id: UUID | None
    zones: tuple[ZonePlace, ...]


@dataclass(frozen=True, slots=True)
class SitePlace:
    """A property shown in the Places view."""

    id: UUID
    name: str
    site_type: SiteType
    spaces: tuple[SpacePlace, ...]


@dataclass(frozen=True, slots=True)
class HouseholdPlaces:
    """The complete place hierarchy for one household."""

    id: UUID
    name: str
    sites: tuple[SitePlace, ...]


def load_place_hierarchy(
    session: Session,
    *,
    household_ids: Sequence[UUID] | None = None,
) -> list[HouseholdPlaces]:
    """Load sites, spaces, and zones grouped beneath each household."""

    if household_ids is not None and not household_ids:
        return []

    household_statement = select(Household).order_by(Household.name)

    if household_ids is not None:
        household_statement = household_statement.where(
            Household.id.in_(household_ids)
        )

    households = session.scalars(household_statement).all()
    selected_household_ids = [household.id for household in households]

    if not selected_household_ids:
        return []

    sites = session.scalars(
        select(Site)
        .where(
            Site.household_id.in_(selected_household_ids),
            Site.active.is_(True),
        )
        .order_by(Site.name)
    ).all()

    site_ids = [site.id for site in sites]

    if site_ids:
        spaces = session.scalars(
            select(Space)
            .where(
                Space.site_id.in_(site_ids),
                Space.active.is_(True),
            )
            .order_by(Space.name)
        ).all()
    else:
        spaces = []

    space_ids = [space.id for space in spaces]

    if space_ids:
        zones = session.scalars(
            select(EnvironmentalZone)
            .where(
                EnvironmentalZone.space_id.in_(space_ids),
                EnvironmentalZone.active.is_(True),
            )
            .order_by(EnvironmentalZone.name)
        ).all()
    else:
        zones = []

    zones_by_space: dict[UUID, list[ZonePlace]] = defaultdict(list)

    for zone in zones:
        zones_by_space[zone.space_id].append(
            ZonePlace(
                id=zone.id,
                name=zone.name,
                zone_type=zone.zone_type,
            )
        )

    spaces_by_site: dict[UUID, list[SpacePlace]] = defaultdict(list)

    for space in spaces:
        spaces_by_site[space.site_id].append(
            SpacePlace(
                id=space.id,
                name=space.name,
                space_type=space.space_type,
                parent_space_id=space.parent_space_id,
                zones=tuple(zones_by_space[space.id]),
            )
        )

    sites_by_household: dict[UUID, list[SitePlace]] = defaultdict(list)

    for site in sites:
        sites_by_household[site.household_id].append(
            SitePlace(
                id=site.id,
                name=site.name,
                site_type=site.site_type,
                spaces=tuple(spaces_by_site[site.id]),
            )
        )

    return [
        HouseholdPlaces(
            id=household.id,
            name=household.name,
            sites=tuple(sites_by_household[household.id]),
        )
        for household in households
    ]