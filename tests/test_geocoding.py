"""Tests for privacy-conscious location search."""

from decimal import Decimal

import httpx
import pytest

from plant_health.weather import (
    GeocodingError,
    OpenMeteoGeocoder,
)


def test_open_meteo_geocoder_parses_location_results() -> None:
    """The geocoder should standardize valid location results."""

    def handle_request(request: httpx.Request) -> httpx.Response:
        assert request.url.params["name"] == "Test City"
        assert request.url.params["count"] == "5"

        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Test City",
                        "admin1": "Test State",
                        "country": "United States",
                        "country_code": "US",
                        "latitude": 42.3,
                        "longitude": -71.7,
                        "elevation": 120,
                        "timezone": "America/New_York",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handle_request)

    with httpx.Client(transport=transport) as client:
        geocoder = OpenMeteoGeocoder(client=client)
        results = geocoder.search("Test City")

    assert len(results) == 1

    result = results[0]

    assert result.display_name == "Test City, Test State, United States"
    assert result.latitude == Decimal("42.3")
    assert result.longitude == Decimal("-71.7")
    assert result.elevation_m == Decimal(120)
    assert result.timezone == "America/New_York"


def test_open_meteo_geocoder_validates_search_query() -> None:
    """Very short searches should be rejected before making a request."""

    geocoder = OpenMeteoGeocoder()

    with pytest.raises(
        GeocodingError,
        match="Enter at least two characters",
    ):
        geocoder.search(" ")