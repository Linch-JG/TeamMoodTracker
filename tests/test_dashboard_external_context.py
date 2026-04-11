"""Tests for the external well-being tip integration."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

import team_mood_tracker.backend.app as backend_app
import team_mood_tracker.backend.external_context as external_context
from team_mood_tracker.backend.api_schemas import WellbeingTip
from team_mood_tracker.backend.external_context import (
    ExternalContextError,
    fetch_dashboard_wellbeing_tip,
)
from team_mood_tracker.frontend import dashboard_context


def test_fetch_dashboard_wellbeing_tip_calls_reflection_api(monkeypatch) -> None:
    """The backend maps the external provider payload into a dashboard tip."""

    captured: dict[str, Any] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self, *_args: Any, **_kwargs: Any) -> bytes:
            return (
                b'[{"q": "Keep your perspective when things get difficult.", '
                b'"a": "Anonymous"}]'
            )

    def fake_urlopen(external_request: Any, timeout: int) -> FakeResponse:
        captured["url"] = external_request.full_url
        captured["headers"] = dict(external_request.header_items())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(external_context.request, "urlopen", fake_urlopen)

    snapshot = fetch_dashboard_wellbeing_tip("https://quotes.example/api")

    assert captured == {
        "url": "https://quotes.example/api",
        "headers": {"Accept": "application/json"},
        "timeout": 5,
    }
    assert snapshot.tip_id == 1
    assert snapshot.advice == "Keep your perspective when things get difficult."
    assert snapshot.author == "Anonymous"
    assert snapshot.source == "ZenQuotes"


def test_wellbeing_tip_endpoint_returns_advice_snapshot(tmp_path, monkeypatch) -> None:
    """GET /dashboard/wellbeing-tip exposes the provider data to the frontend."""

    app = backend_app.create_app(tmp_path / "api.sqlite3")
    expected = WellbeingTip(
        tip_id=1,
        advice="Take a breath before reacting.",
        author="Anonymous",
        source="ZenQuotes",
    )
    monkeypatch.setattr(backend_app, "fetch_dashboard_wellbeing_tip", lambda: expected)

    with TestClient(app) as client:
        response = client.get("/dashboard/wellbeing-tip")

    assert response.status_code == 200
    assert response.json() == {
        "tip_id": 1,
        "advice": "Take a breath before reacting.",
        "author": "Anonymous",
        "source": "ZenQuotes",
    }


def test_wellbeing_tip_endpoint_surfaces_provider_failures(
    tmp_path, monkeypatch
) -> None:
    """Provider failures are returned as a bad gateway response instead of crashing the API."""

    app = backend_app.create_app(tmp_path / "api.sqlite3")

    def raise_provider_error() -> WellbeingTip:
        raise ExternalContextError("Reflection provider request failed.")

    monkeypatch.setattr(
        backend_app, "fetch_dashboard_wellbeing_tip", raise_provider_error
    )

    with TestClient(app) as client:
        response = client.get("/dashboard/wellbeing-tip")

    assert response.status_code == 502
    assert response.json() == {"detail": "Reflection provider request failed."}


def test_fetch_dashboard_wellbeing_tip_calls_backend(monkeypatch) -> None:
    """The Streamlit helper fetches the dashboard widget data from FastAPI."""

    captured: dict[str, Any] = {}
    payload = {
        "tip_id": 1,
        "advice": "Take a breath before reacting.",
        "author": "Anonymous",
        "source": "ZenQuotes",
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

    result = dashboard_context.fetch_dashboard_wellbeing_tip("http://testserver/")

    assert captured == {
        "url": "http://testserver/dashboard/wellbeing-tip",
        "timeout": 5,
    }
    assert result == payload
