"""Location search using the Open-Meteo geocoding API."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx


class GeocodingError(RuntimeError):
    """Raised when a location search cannot be completed."""


@dataclass(frozen=True, slots=True)
class GeocodingResult:
    """A privacy-conscious geographic result for site setup."""

    name: str
    admin_area: str | None
    country: str | None
    country_code: str | None
    latitude: Decimal
    longitude: Decimal
    elevation_m: Decimal | None
    timezone: str

    @property
    def display_name(self) -> str:
        """Return a readable location label."""

        parts = [
            self.name,
            self.admin_area,
            self.country,
        ]
        return ", ".join(part for part in parts if part)


def _to_decimal(value: Any) -> Decimal | None:
    """Convert an API number into a decimal."""

    if value is None:
        return None

    return Decimal(str(value))


class OpenMeteoGeocoder:
    """Search for cities and postal codes without requiring an API key."""

    provider_name = "Open-Meteo"
    base_url = "https://geocoding-api.open-meteo.com/v1/search"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Create a geocoder with an optional injectable HTTP client."""

        self._client = client or httpx.Client()
        self._timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        *,
        count: int = 5,
    ) -> list[GeocodingResult]:
        """Search for matching cities or postal codes."""

        clean_query = query.strip()

        if len(clean_query) < 2:
            raise GeocodingError(
                "Enter at least two characters for the location search."
            )

        if count < 1 or count > 100:
            raise GeocodingError(
                "Location result count must be between 1 and 100."
            )

        try:
            response = self._client.get(
                self.base_url,
                params={
                    "name": clean_query,
                    "count": count,
                    "language": "en",
                    "format": "json",
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise GeocodingError(
                "The location search could not be completed."
            ) from error

        if not isinstance(payload, dict):
            raise GeocodingError(
                "The location provider returned an invalid response."
            )

        raw_results = payload.get("results", [])

        if not isinstance(raw_results, list):
            raise GeocodingError(
                "The location provider returned invalid results."
            )

        results: list[GeocodingResult] = []

        for raw_result in raw_results:
            parsed_result = self._parse_result(raw_result)

            if parsed_result is not None:
                results.append(parsed_result)

        return results

    def _parse_result(
        self,
        raw_result: Any,
    ) -> GeocodingResult | None:
        """Convert one provider result into the shared result format."""

        if not isinstance(raw_result, dict):
            return None

        latitude = _to_decimal(raw_result.get("latitude"))
        longitude = _to_decimal(raw_result.get("longitude"))
        name = raw_result.get("name")
        timezone = raw_result.get("timezone")

        if (
            latitude is None
            or longitude is None
            or not isinstance(name, str)
            or not isinstance(timezone, str)
        ):
            return None

        admin_area = raw_result.get("admin1")
        country = raw_result.get("country")
        country_code = raw_result.get("country_code")

        return GeocodingResult(
            name=name,
            admin_area=admin_area if isinstance(admin_area, str) else None,
            country=country if isinstance(country, str) else None,
            country_code=(
                country_code
                if isinstance(country_code, str)
                else None
            ),
            latitude=latitude,
            longitude=longitude,
            elevation_m=_to_decimal(raw_result.get("elevation")),
            timezone=timezone,
        )