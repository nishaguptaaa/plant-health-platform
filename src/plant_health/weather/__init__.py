"""Weather-provider integrations."""

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
    "OpenMeteoProvider",
    "WeatherCaptureError",
    "WeatherProvider",
    "WeatherProviderError",
    "WeatherReading",
    "capture_current_weather",
]