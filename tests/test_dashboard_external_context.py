"""Tests for the external dashboard context integration."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

import team_mood_tracker.backend.app as backend_app
from team_mood_tracker.backend.api_schemas import ExternalWeatherContext
from team_mood_tracker.backend.external_context import (
    DEFAULT_TEAM_LOCATION_NAME,
    ExternalContextError,
    fetch_dashboard_weather,
)
from team_mood_tracker.frontend import dashboard_context


def test_fetch_dashboard_weather_calls_open_meteo(monkeypatch) -> None:
    """The backend maps the external provider payload into dashboard context."""

    captured: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "current": {
                    "time": "2026-04-11T13:00:00",
                    "temperature_2m": 12.4,
                    "wind_speed_10m": 9.2,
                    "weather_code": 2,
                }
            }

    def fake_get(
        url: str,
        params: dict[str, Any],
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("team_mood_tracker.backend.external_context.requests.get", fake_get)

    snapshot = fetch_dashboard_weather("https://weather.example/api")

    assert captured == {
        "url": "https://weather.example/api",
        "params": {
            "latitude": 55.7522,
            "longitude": 49.1114,
            "current": "temperature_2m,wind_speed_10m,weather_code",
            "timezone": "auto",
        },
        "timeout": 5,
    }
    assert snapshot.location_name == DEFAULT_TEAM_LOCATION_NAME
    assert snapshot.temperature_celsius == 12.4
    assert snapshot.wind_speed_kph == 9.2
    assert snapshot.weather_summary == "Partly cloudy"
    assert snapshot.source == "Open-Meteo"


def test_external_context_endpoint_returns_weather_snapshot(tmp_path, monkeypatch) -> None:
    """GET /dashboard/external-context exposes the provider data to the frontend."""

    app = backend_app.create_app(tmp_path / "api.sqlite3")
    expected = ExternalWeatherContext(
        location_name="Team HQ",
        temperature_celsius=14.0,
        wind_speed_kph=8.0,
        weather_summary="Clear sky",
        observed_at="2026-04-11T14:00:00",
        source="Open-Meteo",
    )
    monkeypatch.setattr(backend_app, "fetch_dashboard_weather", lambda: expected)

    with TestClient(app) as client:
        response = client.get("/dashboard/external-context")

    assert response.status_code == 200
    assert response.json() == {
        "location_name": "Team HQ",
        "temperature_celsius": 14.0,
        "wind_speed_kph": 8.0,
        "weather_summary": "Clear sky",
        "observed_at": "2026-04-11T14:00:00",
        "source": "Open-Meteo",
    }


def test_external_context_endpoint_surfaces_provider_failures(tmp_path, monkeypatch) -> None:
    """Provider failures are returned as a bad gateway response instead of crashing the API."""

    app = backend_app.create_app(tmp_path / "api.sqlite3")

    def raise_provider_error() -> ExternalWeatherContext:
        raise ExternalContextError("Weather provider request failed.")

    monkeypatch.setattr(backend_app, "fetch_dashboard_weather", raise_provider_error)

    with TestClient(app) as client:
        response = client.get("/dashboard/external-context")

    assert response.status_code == 502
    assert response.json() == {"detail": "Weather provider request failed."}


def test_fetch_dashboard_external_context_calls_backend(monkeypatch) -> None:
    """The Streamlit helper fetches the dashboard widget data from FastAPI."""

    captured: dict[str, Any] = {}
    payload = {
        "location_name": "Team HQ",
        "temperature_celsius": 14.0,
        "wind_speed_kph": 8.0,
        "weather_summary": "Clear sky",
        "observed_at": "2026-04-11T14:00:00",
        "source": "Open-Meteo",
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return payload

    def fake_get(url: str, timeout: int) -> FakeResponse:
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(dashboard_context.requests, "get", fake_get)

    result = dashboard_context.fetch_dashboard_external_context("http://testserver/")

    assert captured == {
        "url": "http://testserver/dashboard/external-context",
        "timeout": 5,
    }
    assert result == payload
