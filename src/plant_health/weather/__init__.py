"""Weather-provider and location-search integrations."""

from plant_health.weather.geocoding import (
    GeocodingError,
    GeocodingResult,
    OpenMeteoGeocoder,
)
from plant_health.weather.open_meteo import OpenMeteoProvider
from plant_health.weather.provider import (
    WeatherProvider,
    WeatherProviderError,
    WeatherReading,
)
from plant_health.weather.service import (
    WeatherCaptureError,
    capture_current_weather,
)

__all__ = [
    "GeocodingError",
    "GeocodingResult",
    "OpenMeteoGeocoder",
    "OpenMeteoProvider",
    "WeatherCaptureError",
    "WeatherProvider",
    "WeatherProviderError",
    "WeatherReading",
    "capture_current_weather",
]