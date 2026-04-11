"""Tests for mood history frontend functions."""

from __future__ import annotations

from typing import Any

from team_mood_tracker.frontend import history_view


def test_fetch_mood_entries_calls_api(monkeypatch) -> None:
    """Fetch mood entries sends request to the API with correct parameters."""

    captured: dict[str, Any] = {}
    expected_entries = [
        {
            "id": 1,
            "user": "Alice",
            "mood": "happy",
            "rating": 5,
            "comment": "Great day!",
            "created_at": "2026-04-10T18:00:00+00:00",
        }
    ]

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> list[dict[str, Any]]:
            return expected_entries

    def fake_get(url: str, params: dict[str, Any], timeout: int) -> FakeResponse:
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(history_view.requests, "get", fake_get)

    result = history_view.fetch_mood_entries(
        api_base_url="http://testserver/",
        user="Alice",
        date_from="2026-04-01",
        date_to="2026-04-10",
        sort_by="rating",
        order="asc",
    )

    assert captured["url"] == "http://testserver/mood-entries"
    assert captured["params"] == {
        "user": "Alice",
        "date_from": "2026-04-01",
        "date_to": "2026-04-10",
        "sort_by": "rating",
        "order": "asc",
    }
    assert captured["timeout"] == 5
    assert result == expected_entries


def test_update_mood_entry_calls_api(monkeypatch) -> None:
    """Update mood entry sends PUT request to the API."""

    captured: dict[str, Any] = {}
    update_data = {"mood": "neutral", "rating": 3}
    expected_response = {
        "id": 1,
        "user": "Alice",
        "mood": "neutral",
        "rating": 3,
        "comment": "Updated",
        "created_at": "2026-04-10T18:00:00+00:00",
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return expected_response

    def fake_put(url: str, json: dict[str, Any], timeout: int) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(history_view.requests, "put", fake_put)

    result = history_view.update_mood_entry(
        entry_id=1,
        update_data=update_data,
        api_base_url="http://testserver/",
    )

    assert captured["url"] == "http://testserver/mood-entries/1"
    assert captured["json"] == update_data
    assert captured["timeout"] == 5
    assert result == expected_response


def test_delete_mood_entry_api_calls_delete(monkeypatch) -> None:
    """Delete mood entry sends DELETE request to the API."""

    captured: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    def fake_delete(url: str, timeout: int) -> FakeResponse:
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(history_view.requests, "delete", fake_delete)

    history_view.delete_mood_entry_api(
        entry_id=1,
        api_base_url="http://testserver/",
    )

    assert captured["url"] == "http://testserver/mood-entries/1"
    assert captured["timeout"] == 5


def test_get_api_base_url_uses_parameter() -> None:
    """Get API base URL prefers the parameter over environment."""

    result = history_view.get_api_base_url("http://custom:9000")

    assert result == "http://custom:9000/"


def test_get_api_base_url_uses_default(monkeypatch) -> None:
    """Get API base URL uses default when no parameter or env var."""

    monkeypatch.delenv(history_view.API_BASE_URL_ENV, raising=False)

    result = history_view.get_api_base_url()

    assert result == "http://localhost:8000/"
