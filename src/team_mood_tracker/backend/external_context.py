"""External API integration for lightweight dashboard context."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import requests

from team_mood_tracker.backend.api_schemas import ExternalWeatherContext


EXTERNAL_WEATHER_API_URL_ENV = "TEAM_MOOD_EXTERNAL_WEATHER_API_URL"
TEAM_LOCATION_NAME_ENV = "TEAM_MOOD_LOCATION_NAME"
TEAM_LOCATION_LATITUDE_ENV = "TEAM_MOOD_LOCATION_LATITUDE"
TEAM_LOCATION_LONGITUDE_ENV = "TEAM_MOOD_LOCATION_LONGITUDE"
DEFAULT_EXTERNAL_WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TEAM_LOCATION_NAME = "Configured Team Location"
DEFAULT_TEAM_LOCATION_LATITUDE = 55.7522
DEFAULT_TEAM_LOCATION_LONGITUDE = 49.1114
EXTERNAL_REQUEST_TIMEOUT_SECONDS = 5
WEATHER_CODE_SUMMARIES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass(frozen=True, slots=True)
class TeamLocation:
    """Coordinates used for the dashboard weather widget."""

    name: str
    latitude: float
    longitude: float


class ExternalContextError(RuntimeError):
    """Raised when the external weather provider cannot be used safely."""


def get_team_location() -> TeamLocation:
    """Return the configured location for dashboard context lookups."""

    return TeamLocation(
        name=os.getenv(TEAM_LOCATION_NAME_ENV, DEFAULT_TEAM_LOCATION_NAME),
        latitude=float(os.getenv(TEAM_LOCATION_LATITUDE_ENV, DEFAULT_TEAM_LOCATION_LATITUDE)),
        longitude=float(os.getenv(TEAM_LOCATION_LONGITUDE_ENV, DEFAULT_TEAM_LOCATION_LONGITUDE)),
    )


def describe_weather_code(weather_code: int) -> str:
    """Translate an Open-Meteo weather code into a short label."""

    return WEATHER_CODE_SUMMARIES.get(weather_code, f"Weather code {weather_code}")


def fetch_dashboard_weather(base_url: str | None = None) -> ExternalWeatherContext:
    """Fetch current weather data for the configured team location."""

    location = get_team_location()
    response = _perform_weather_request(location, base_url)
    payload = response.json()
    current = payload.get("current")
    if not isinstance(current, dict):
        raise ExternalContextError("Weather provider did not return current conditions.")

    try:
        observed_at = datetime.fromisoformat(str(current["time"]))
        weather_code = int(current["weather_code"])
        temperature_celsius = float(current["temperature_2m"])
        wind_speed_kph = float(current["wind_speed_10m"])
    except (KeyError, TypeError, ValueError) as error:
        raise ExternalContextError("Weather provider response schema was not recognized.") from error

    return ExternalWeatherContext(
        location_name=location.name,
        temperature_celsius=temperature_celsius,
        wind_speed_kph=wind_speed_kph,
        weather_summary=describe_weather_code(weather_code),
        observed_at=observed_at,
        source="Open-Meteo",
    )


def _perform_weather_request(
    location: TeamLocation,
    base_url: str | None = None,
) -> requests.Response:
    """Perform the outbound request to the weather provider."""

    weather_api_url = base_url or os.getenv(
        EXTERNAL_WEATHER_API_URL_ENV,
        DEFAULT_EXTERNAL_WEATHER_API_URL,
    )
    try:
        response = requests.get(
            weather_api_url,
            params={
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": "temperature_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
            timeout=EXTERNAL_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise ExternalContextError("Weather provider request failed.") from error

    return response
