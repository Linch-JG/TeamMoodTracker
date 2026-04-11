"""Tests for submission form helpers."""

from __future__ import annotations

from typing import Any

from team_mood_tracker.frontend import submission_form


def test_submit_mood_entry_calls_api(monkeypatch) -> None:
    """submit_mood_entry sends POST request to the API."""

    captured: dict[str, Any] = {}
    payload = {"user": "Alice", "mood": "happy", "rating": 5, "comment": None}
    expected_response = {
        "id": 1,
        **payload,
        "created_at": "2026-04-10T18:00:00+00:00",
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return expected_response

    def fake_post(url: str, json: dict[str, Any], timeout: int) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(submission_form.requests, "post", fake_post)

    result = submission_form.submit_mood_entry(payload, "http://testserver/")

    assert captured["url"] == "http://testserver/mood-entries"
    assert captured["json"] == payload
    assert captured["timeout"] == 5
    assert result == expected_response


def test_submit_mood_entry_uses_env_url(monkeypatch) -> None:
    """submit_mood_entry uses environment variable for API URL when not provided."""

    monkeypatch.setenv(submission_form.API_BASE_URL_ENV, "http://custom:9000")
    captured: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"id": 1}

    def fake_post(url: str, json: dict[str, Any], timeout: int) -> FakeResponse:
        captured["url"] = url
        return FakeResponse()

    monkeypatch.setattr(submission_form.requests, "post", fake_post)

    submission_form.submit_mood_entry({"user": "test", "mood": "happy", "rating": 5})

    assert captured["url"] == "http://custom:9000/mood-entries"
