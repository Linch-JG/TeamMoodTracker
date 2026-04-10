"""Tests for the mood submission flow."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

from team_mood_tracker.backend.app import create_app
from team_mood_tracker.backend.database import create_mood_entry
from team_mood_tracker.backend.schemas import MoodEntryCreate
from team_mood_tracker.frontend import submission_form


def test_create_mood_entry_saves_to_sqlite(tmp_path) -> None:
    """The repository creates the table and stores a submitted mood entry."""

    database_path = tmp_path / "moods.sqlite3"
    saved_entry = create_mood_entry(
        MoodEntryCreate(
            user="Alex",
            mood="happy",
            rating=5,
            comment="Sprint demo went well.",
        ),
        database_path,
    )

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT id, user, mood, rating, comment, created_at
            FROM mood_entries
            WHERE id = ?
            """,
            (saved_entry.id,),
        ).fetchone()

    assert row == (
        saved_entry.id,
        "Alex",
        "happy",
        5,
        "Sprint demo went well.",
        saved_entry.created_at.isoformat(),
    )
    assert datetime.fromisoformat(row[5]) == saved_entry.created_at


def test_submit_mood_entry_endpoint_persists_entry(tmp_path) -> None:
    """POST /mood-entries validates input and writes the entry to SQLite."""

    database_path = tmp_path / "api.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        response = client.post(
            "/mood-entries",
            json={
                "user": "Alex",
                "mood": "stressed",
                "rating": 2,
                "comment": "Two deadlines today.",
            },
        )

    assert response.status_code == 201
    response_body = response.json()
    assert response_body["id"] == 1
    assert response_body["user"] == "Alex"
    assert response_body["mood"] == "stressed"
    assert response_body["rating"] == 2
    assert response_body["comment"] == "Two deadlines today."
    assert datetime.fromisoformat(response_body["created_at"])

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT user, mood, rating, comment
            FROM mood_entries
            WHERE id = ?
            """,
            (response_body["id"],),
        ).fetchone()

    assert row == ("Alex", "stressed", 2, "Two deadlines today.")


def test_submit_mood_entry_endpoint_rejects_invalid_rating(tmp_path) -> None:
    """Invalid ratings are rejected before anything is stored."""

    database_path = tmp_path / "validation.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        response = client.post(
            "/mood-entries",
            json={
                "user": "Alex",
                "mood": "happy",
                "rating": 6,
                "comment": None,
            },
        )

    assert response.status_code == 422

    with sqlite3.connect(database_path) as connection:
        stored_count = connection.execute("SELECT COUNT(*) FROM mood_entries").fetchone()[0]

    assert stored_count == 0


def test_streamlit_submit_helper_posts_to_backend(monkeypatch) -> None:
    """The frontend helper sends the form payload to the create endpoint."""

    payload = {"user": "Alex", "mood": "neutral", "rating": 3, "comment": None}
    captured: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"id": 7, **payload, "created_at": "2026-04-10T18:00:00+00:00"}

    def fake_post(url: str, json: dict[str, Any], timeout: int) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(submission_form.requests, "post", fake_post)

    result = submission_form.submit_mood_entry(payload, "http://testserver/")

    assert captured == {
        "url": "http://testserver/mood-entries",
        "json": payload,
        "timeout": 5,
    }
    assert result["id"] == 7
    assert result["user"] == "Alex"
