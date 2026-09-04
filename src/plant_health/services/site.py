"""Services for creating physical plant sites."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plant_health.database.models import (
    Household,
    Site,
    SiteType,
    TerrainPosition,
)


class SiteSetupError(ValueError):
    """Raised when site setup information is invalid."""


def _required_text(value: str, *, field_name: str) -> str:
    """Remove surrounding whitespace and reject empty text."""

    cleaned_value = value.strip()

    if not cleaned_value:
        raise SiteSetupError(f"{field_name} is required.")

    return cleaned_value


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values."""

    if value is None:
        return None

    cleaned_value = value.strip()
    return cleaned_value or None


def _validate_timezone(timezone: str) -> str:
    """Require a valid IANA timezone name."""

    clean_timezone = _required_text(
        timezone,
        field_name="Timezone",
    )

    try:
        ZoneInfo(clean_timezone)
    except ZoneInfoNotFoundError as error:
        raise SiteSetupError(
            "Enter a valid timezone such as America/New_York."
        ) from error

    return clean_timezone


def _validate_coordinates(
    latitude: Decimal | None,
    longitude: Decimal | None,
) -> None:
    """Validate an optional latitude and longitude pair."""

    if (latitude is None) != (longitude is None):
        raise SiteSetupError(
            "Latitude and longitude must either both be provided or both be blank."
        )

    if latitude is not None and not Decimal(-90) <= latitude <= Decimal(90):
        raise SiteSetupError("Latitude must be between -90 and 90.")

    if (
        longitude is not None
        and not Decimal(-180) <= longitude <= Decimal(180)
    ):
        raise SiteSetupError("Longitude must be between -180 and 180.")


def create_site(
    session: Session,
    *,
    household_id: UUID,
    name: str,
    site_type: SiteType,
    timezone: str,
    address_text: str | None = None,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
    elevation_m: Decimal | None = None,
    terrain_position: TerrainPosition = TerrainPosition.UNKNOWN,
    terrain_slope_degrees: Decimal | None = None,
    weather_enabled: bool = False,
    weather_provider: str = "open_meteo",
    weather_sync_interval_minutes: int = 60,
) -> Site:
    """Create and save a site belonging to one household."""

    clean_name = _required_text(name, field_name="Site name")
    clean_timezone = _validate_timezone(timezone)
    clean_address = _optional_text(address_text)
    clean_weather_provider = _required_text(
        weather_provider,
        field_name="Weather provider",
    )

    _validate_coordinates(latitude, longitude)

    if elevation_m is not None and not (
        Decimal(-500) <= elevation_m <= Decimal(9000)
    ):
        raise SiteSetupError(
            "Elevation must be between -500 and 9000 meters."
        )

    if terrain_slope_degrees is not None and not (
        Decimal(0) <= terrain_slope_degrees <= Decimal(90)
    ):
        raise SiteSetupError(
            "Terrain slope must be between 0 and 90 degrees."
        )

    if weather_sync_interval_minutes < 15:
        raise SiteSetupError(
            "Weather synchronization must be at least 15 minutes."
        )

    if weather_enabled and latitude is None:
        raise SiteSetupError(
            "Weather tracking requires latitude and longitude."
        )

    household = session.get(Household, household_id)

    if household is None:
        raise SiteSetupError("The selected household does not exist.")

    existing_site = session.scalar(
        select(Site).where(
            Site.household_id == household_id,
            Site.name == clean_name,
        )
    )

    if existing_site is not None:
        raise SiteSetupError(
            "A site with this name already exists in the household."
        )

    site = Site(
        household_id=household_id,
        name=clean_name,
        site_type=site_type,
        address_text=clean_address,
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation_m,
        terrain_position=terrain_position,
        terrain_slope_degrees=terrain_slope_degrees,
        timezone=clean_timezone,
        weather_enabled=weather_enabled,
        weather_provider=clean_weather_provider,
        weather_sync_interval_minutes=weather_sync_interval_minutes,
        active=True,
    )

    try:
        session.add(site)
        session.commit()
        session.refresh(site)
    except IntegrityError as error:
        session.rollback()
        raise SiteSetupError("The site could not be saved.") from error
    except Exception:
        session.rollback()
        raise

    return site