"""Application services for retrieving and saving site weather."""

from __future__ import annotations

from sqlalchemy.orm import Session

from plant_health.database.models.site import Site
from plant_health.database.models.weather import (
    WeatherRecordType,
    WeatherSnapshot,
)
from plant_health.weather.provider import WeatherProvider


class WeatherCaptureError(RuntimeError):
    """Raised when a site cannot be used to capture weather."""


def capture_current_weather(
    session: Session,
    *,
    site: Site,
    provider: WeatherProvider,
) -> WeatherSnapshot:
    """Retrieve current weather for a site and save it to the database."""

    if not site.weather_enabled:
        raise WeatherCaptureError(
            f"Weather tracking is disabled for site {site.name!r}."
        )

    if site.latitude is None or site.longitude is None:
        raise WeatherCaptureError(
            f"Site {site.name!r} needs latitude and longitude."
        )

    elevation_m = (
        float(site.elevation_m)
        if site.elevation_m is not None
        else None
    )

    reading = provider.fetch_current(
        latitude=float(site.latitude),
        longitude=float(site.longitude),
        timezone=site.timezone,
        elevation_m=elevation_m,
    )

    snapshot = WeatherSnapshot(
        site_id=site.id,
        measured_at=reading.measured_at,
        retrieved_at=reading.retrieved_at,
        record_type=WeatherRecordType.OBSERVED,
        provider_name=reading.provider_name,
        provider_weather_code=reading.provider_weather_code,
        condition=reading.condition,
        is_daylight=reading.is_daylight,
        temperature_c=reading.temperature_c,
        apparent_temperature_c=reading.apparent_temperature_c,
        relative_humidity_pct=reading.relative_humidity_pct,
        cloud_cover_pct=reading.cloud_cover_pct,
        precipitation_probability_pct=(
            reading.precipitation_probability_pct
        ),
        precipitation_mm=reading.precipitation_mm,
        wind_speed_kph=reading.wind_speed_kph,
        wind_direction_degrees=reading.wind_direction_degrees,
        surface_pressure_hpa=reading.surface_pressure_hpa,
        solar_radiation_w_m2=reading.solar_radiation_w_m2,
        uv_index=reading.uv_index,
    )

    try:
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
    except Exception:
        session.rollback()
        raise

    return snapshot