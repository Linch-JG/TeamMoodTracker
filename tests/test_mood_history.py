"""Tests for mood history management (CRUD operations)."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from team_mood_tracker.backend.app import create_app
from team_mood_tracker.backend.database import (
    create_mood_entry,
    delete_mood_entry,
    get_mood_entry_by_id,
    list_mood_entries,
    MoodEntryNotFoundError,
    update_mood_entry,
)
from team_mood_tracker.backend.schemas import MoodEntryCreate, MoodEntryUpdate


def test_list_mood_entries_returns_all_entries(tmp_path) -> None:
    """List mood entries returns all entries in the database."""

    database_path = tmp_path / "list_all.sqlite3"

    entry1 = create_mood_entry(
        MoodEntryCreate(user="Alice", mood="happy", rating=5, comment="Great day!"),
        database_path,
    )
    entry2 = create_mood_entry(
        MoodEntryCreate(user="Bob", mood="stressed", rating=2, comment="Tough day."),
        database_path,
    )

    entries = list_mood_entries(database_path)

    assert len(entries) == 2
    entry_ids = {entry.id for entry in entries}
    assert entry_ids == {entry1.id, entry2.id}


def test_list_mood_entries_filters_by_user(tmp_path) -> None:
    """List mood entries can filter by user name."""

    database_path = tmp_path / "filter_user.sqlite3"

    create_mood_entry(
        MoodEntryCreate(user="Alice", mood="happy", rating=5, comment="Great day!"),
        database_path,
    )
    bob_entry = create_mood_entry(
        MoodEntryCreate(user="Bob", mood="stressed", rating=2, comment="Tough day."),
        database_path,
    )

    entries = list_mood_entries(database_path, user="Bob")

    assert len(entries) == 1
    assert entries[0].id == bob_entry.id
    assert entries[0].user == "Bob"


def test_list_mood_entries_filters_by_date_range(tmp_path) -> None:
    """List mood entries can filter by date range."""

    database_path = tmp_path / "filter_date.sqlite3"

    with sqlite3.connect(database_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                mood TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """)
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Alice", "happy", 5, "Old entry", "2026-04-01T10:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Bob", "neutral", 3, "Recent entry", "2026-04-10T15:00:00+00:00"),
        )

    entries = list_mood_entries(database_path, date_from="2026-04-10")

    assert len(entries) == 1
    assert entries[0].user == "Bob"


def test_list_mood_entries_filters_by_date_to(tmp_path) -> None:
    """List mood entries can filter by date_to parameter."""

    database_path = tmp_path / "filter_date_to.sqlite3"

    with sqlite3.connect(database_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                mood TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """)
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Alice", "happy", 5, "Old entry", "2026-04-01T10:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Bob", "neutral", 3, "Recent entry", "2026-04-10T15:00:00+00:00"),
        )

    entries = list_mood_entries(database_path, date_to="2026-04-05")

    assert len(entries) == 1
    assert entries[0].user == "Alice"


def test_list_mood_entries_sorts_by_date(tmp_path) -> None:
    """List mood entries can sort by date in ascending or descending order."""

    database_path = tmp_path / "sort_date.sqlite3"

    with sqlite3.connect(database_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                mood TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """)
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Alice", "happy", 5, "First", "2026-04-10T10:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Bob", "neutral", 3, "Second", "2026-04-11T15:00:00+00:00"),
        )

    entries_asc = list_mood_entries(database_path, sort_by="date", order="asc")
    assert entries_asc[0].comment == "First"
    assert entries_asc[1].comment == "Second"

    entries_desc = list_mood_entries(database_path, sort_by="date", order="desc")
    assert entries_desc[0].comment == "Second"
    assert entries_desc[1].comment == "First"


def test_list_mood_entries_sorts_by_rating(tmp_path) -> None:
    """List mood entries can sort by rating."""

    database_path = tmp_path / "sort_rating.sqlite3"

    create_mood_entry(
        MoodEntryCreate(user="Alice", mood="happy", rating=5, comment="High rating"),
        database_path,
    )
    create_mood_entry(
        MoodEntryCreate(user="Bob", mood="stressed", rating=2, comment="Low rating"),
        database_path,
    )

    entries_asc = list_mood_entries(database_path, sort_by="rating", order="asc")
    assert entries_asc[0].rating == 2
    assert entries_asc[1].rating == 5

    entries_desc = list_mood_entries(database_path, sort_by="rating", order="desc")
    assert entries_desc[0].rating == 5
    assert entries_desc[1].rating == 2


def test_get_mood_entry_by_id_returns_entry(tmp_path) -> None:
    """Get mood entry by ID returns the correct entry."""

    database_path = tmp_path / "get_by_id.sqlite3"

    created = create_mood_entry(
        MoodEntryCreate(user="Alice", mood="happy", rating=5, comment="Test entry"),
        database_path,
    )

    retrieved = get_mood_entry_by_id(created.id, database_path)

    assert retrieved.id == created.id
    assert retrieved.user == "Alice"
    assert retrieved.mood == "happy"
    assert retrieved.rating == 5
    assert retrieved.comment == "Test entry"


def test_get_mood_entry_by_id_raises_not_found(tmp_path) -> None:
    """Get mood entry by ID raises exception when entry does not exist."""

    database_path = tmp_path / "not_found.sqlite3"

    with pytest.raises(MoodEntryNotFoundError) as exc_info:
        get_mood_entry_by_id(999, database_path)

    assert "999" in str(exc_info.value)


def test_update_mood_entry_modifies_fields(tmp_path) -> None:
    """Update mood entry modifies the specified fields."""

    database_path = tmp_path / "update.sqlite3"

    created = create_mood_entry(
        MoodEntryCreate(user="Alice", mood="happy", rating=5, comment="Original"),
        database_path,
    )

    update = MoodEntryUpdate(mood="neutral", rating=3, comment="Updated")
    updated = update_mood_entry(created.id, update, database_path)

    assert updated.id == created.id
    assert updated.user == "Alice"
    assert updated.mood == "neutral"
    assert updated.rating == 3
    assert updated.comment == "Updated"


def test_update_mood_entry_raises_not_found(tmp_path) -> None:
    """Update mood entry raises exception when entry does not exist."""

    database_path = tmp_path / "update_not_found.sqlite3"

    update = MoodEntryUpdate(mood="neutral")

    with pytest.raises(MoodEntryNotFoundError) as exc_info:
        update_mood_entry(999, update, database_path)

    assert "999" in str(exc_info.value)


def test_delete_mood_entry_removes_entry(tmp_path) -> None:
    """Delete mood entry removes the entry from the database."""

    database_path = tmp_path / "delete.sqlite3"

    created = create_mood_entry(
        MoodEntryCreate(user="Alice", mood="happy", rating=5, comment="To delete"),
        database_path,
    )

    delete_mood_entry(created.id, database_path)

    with pytest.raises(MoodEntryNotFoundError):
        get_mood_entry_by_id(created.id, database_path)


def test_delete_mood_entry_raises_not_found(tmp_path) -> None:
    """Delete mood entry raises exception when entry does not exist."""

    database_path = tmp_path / "delete_not_found.sqlite3"

    with pytest.raises(MoodEntryNotFoundError) as exc_info:
        delete_mood_entry(999, database_path)

    assert "999" in str(exc_info.value)


def test_update_mood_entry_with_no_fields(tmp_path) -> None:
    """Update mood entry with no fields returns the original entry unchanged."""

    database_path = tmp_path / "update_no_fields.sqlite3"

    created = create_mood_entry(
        MoodEntryCreate(user="Alice", mood="happy", rating=5, comment="Original"),
        database_path,
    )

    update = MoodEntryUpdate()
    updated = update_mood_entry(created.id, update, database_path)

    assert updated.id == created.id
    assert updated.user == "Alice"
    assert updated.mood == "happy"
    assert updated.rating == 5
    assert updated.comment == "Original"


def test_get_daily_trends_returns_aggregated_data(tmp_path) -> None:
    """Get daily trends returns aggregated mood ratings per day."""

    database_path = tmp_path / "daily_trends.sqlite3"

    with sqlite3.connect(database_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                mood TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """)
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Alice", "happy", 5, "Good", "2026-04-10T10:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Bob", "stressed", 2, "Bad", "2026-04-10T15:00:00+00:00"),
        )
        conn.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Charlie", "neutral", 4, "OK", "2026-04-11T10:00:00+00:00"),
        )

    from team_mood_tracker.backend.database import get_daily_trends

    trends = get_daily_trends(database_path)

    assert len(trends) == 2
    assert trends[0].date == "2026-04-10"
    assert trends[0].average_rating == 3.5
    assert trends[1].date == "2026-04-11"
    assert trends[1].average_rating == 4.0


def test_list_mood_entries_endpoint_returns_all(tmp_path) -> None:
    """GET /mood-entries returns all mood entries."""

    database_path = tmp_path / "api_list.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        client.post(
            "/mood-entries",
            json={"user": "Alice", "mood": "happy", "rating": 5, "comment": "Test 1"},
        )
        client.post(
            "/mood-entries",
            json={"user": "Bob", "mood": "stressed", "rating": 2, "comment": "Test 2"},
        )

        response = client.get("/mood-entries")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 2


def test_list_mood_entries_endpoint_filters_by_user(tmp_path) -> None:
    """GET /mood-entries with user parameter filters results."""

    database_path = tmp_path / "api_filter.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        client.post(
            "/mood-entries",
            json={"user": "Alice", "mood": "happy", "rating": 5, "comment": "Test 1"},
        )
        client.post(
            "/mood-entries",
            json={"user": "Bob", "mood": "stressed", "rating": 2, "comment": "Test 2"},
        )

        response = client.get("/mood-entries?user=Bob")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["user"] == "Bob"


def test_get_mood_entry_endpoint_returns_entry(tmp_path) -> None:
    """GET /mood-entries/{id} returns the specified entry."""

    database_path = tmp_path / "api_get.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        create_response = client.post(
            "/mood-entries",
            json={"user": "Alice", "mood": "happy", "rating": 5, "comment": "Test"},
        )
        entry_id = create_response.json()["id"]

        response = client.get(f"/mood-entries/{entry_id}")

    assert response.status_code == 200
    entry = response.json()
    assert entry["id"] == entry_id
    assert entry["user"] == "Alice"


def test_get_mood_entry_endpoint_returns_404(tmp_path) -> None:
    """GET /mood-entries/{id} returns 404 when entry does not exist."""

    database_path = tmp_path / "api_get_404.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        response = client.get("/mood-entries/999")

    assert response.status_code == 404


def test_update_mood_entry_endpoint_modifies_fields(tmp_path) -> None:
    """PUT /mood-entries/{id} updates the specified fields."""

    database_path = tmp_path / "api_update.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        create_response = client.post(
            "/mood-entries",
            json={"user": "Alice", "mood": "happy", "rating": 5, "comment": "Original"},
        )
        entry_id = create_response.json()["id"]

        update_response = client.put(
            f"/mood-entries/{entry_id}",
            json={"mood": "neutral", "rating": 3},
        )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id"] == entry_id
    assert updated["user"] == "Alice"
    assert updated["mood"] == "neutral"
    assert updated["rating"] == 3


def test_update_mood_entry_endpoint_returns_404(tmp_path) -> None:
    """PUT /mood-entries/{id} returns 404 when entry does not exist."""

    database_path = tmp_path / "api_update_404.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        response = client.put(
            "/mood-entries/999",
            json={"mood": "neutral"},
        )

    assert response.status_code == 404


def test_delete_mood_entry_endpoint_removes_entry(tmp_path) -> None:
    """DELETE /mood-entries/{id} removes the entry."""

    database_path = tmp_path / "api_delete.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        create_response = client.post(
            "/mood-entries",
            json={
                "user": "Alice",
                "mood": "happy",
                "rating": 5,
                "comment": "To delete",
            },
        )
        entry_id = create_response.json()["id"]

        delete_response = client.delete(f"/mood-entries/{entry_id}")
        assert delete_response.status_code == 204

        get_response = client.get(f"/mood-entries/{entry_id}")
        assert get_response.status_code == 404


def test_delete_mood_entry_endpoint_returns_404(tmp_path) -> None:
    """DELETE /mood-entries/{id} returns 404 when entry does not exist."""

    database_path = tmp_path / "api_delete_404.sqlite3"
    app = create_app(database_path)

    with TestClient(app) as client:
        response = client.delete("/mood-entries/999")

    assert response.status_code == 404
