"""Tests for dashboard context helpers."""

from __future__ import annotations

from typing import Any

from team_mood_tracker.frontend import dashboard_context


def test_fetch_dashboard_wellbeing_tip_uses_env(monkeypatch) -> None:
    """fetch_dashboard_wellbeing_tip uses environment variable when not provided."""

    monkeypatch.setenv(dashboard_context.API_BASE_URL_ENV, "http://custom:9000")
    captured: dict[str, Any] = {}
    expected_response = {
        "tip_id": 1,
        "advice": "Test advice",
        "author": "Test Author",
        "source": "Test Source",
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return expected_response

    def fake_get(url: str, timeout: int) -> FakeResponse:
        captured["url"] = url
        return FakeResponse()

    monkeypatch.setattr(dashboard_context.requests, "get", fake_get)

    result = dashboard_context.fetch_dashboard_wellbeing_tip()

    assert captured["url"] == "http://custom:9000/dashboard/wellbeing-tip"
    assert result == expected_response
