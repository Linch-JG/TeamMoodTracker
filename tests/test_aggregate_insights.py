"""Tests for aggregate analytics insights (average mood and distributions)."""

from __future__ import annotations

import sqlite3
from datetime import date

from fastapi.testclient import TestClient

from team_mood_tracker.backend.app import create_app
from team_mood_tracker.backend.database import (
    get_average_mood_insight,
    get_mood_distribution,
    initialize_database,
)


def _seed_entries(database_path) -> None:
    """Insert deterministic mood records with fixed dates for analytics tests."""

    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Alice", "happy", 5, "Great day", "2026-04-10T10:00:00+00:00"),
        )
        connection.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Bob", "stressed", 1, "Tough day", "2026-04-10T15:00:00+00:00"),
        )
        connection.execute(
            "INSERT INTO mood_entries (user, mood, rating, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Cara", "neutral", 4, "Steady", "2026-04-11T09:00:00+00:00"),
        )


def test_get_average_mood_insight_respects_period_filter(tmp_path) -> None:
    """Average mood insight returns filtered aggregates for selected dates."""

    database_path = tmp_path / "aggregate_average.sqlite3"
    _seed_entries(database_path)

    full = get_average_mood_insight(database_path)
    assert full.total_entries == 3
    assert full.average_rating == 10 / 3

    filtered = get_average_mood_insight(
        database_path,
        date_from=date(2026, 4, 10),
        date_to=date(2026, 4, 10),
    )
    assert filtered.date_from == "2026-04-10"
    assert filtered.date_to == "2026-04-10"
    assert filtered.total_entries == 2
    assert filtered.average_rating == 3.0


def test_get_mood_distribution_supports_day_and_period(tmp_path) -> None:
    """Mood distribution supports daily and range-based slices."""

    database_path = tmp_path / "aggregate_distribution.sqlite3"
    _seed_entries(database_path)

    day_distribution = get_mood_distribution(
        database_path,
        target_date=date(2026, 4, 10),
    )
    day_counts = {item.mood: item.count for item in day_distribution}
    assert day_counts == {"happy": 1, "stressed": 1}

    period_distribution = get_mood_distribution(
        database_path,
        date_from=date(2026, 4, 11),
        date_to=date(2026, 4, 11),
    )
    assert len(period_distribution) == 1
    assert period_distribution[0].mood == "neutral"
    assert period_distribution[0].count == 1


def test_aggregate_analytics_endpoints_return_expected_payloads(tmp_path) -> None:
    """Aggregate analytics endpoints return data compatible with frontend widgets."""

    database_path = tmp_path / "aggregate_api.sqlite3"
    _seed_entries(database_path)
    app = create_app(database_path)

    with TestClient(app) as client:
        average_response = client.get(
            "/analytics/average-mood?date_from=2026-04-10&date_to=2026-04-10"
        )
        distribution_response = client.get(
            "/analytics/mood-distribution?target_date=2026-04-10"
        )

    assert average_response.status_code == 200
    average_payload = average_response.json()
    assert average_payload["average_rating"] == 3.0
    assert average_payload["total_entries"] == 2

    assert distribution_response.status_code == 200
    distribution_payload = distribution_response.json()
    assert distribution_payload == [
        {"mood": "happy", "count": 1},
        {"mood": "stressed", "count": 1},
    ]


def test_analytics_openapi_operations_have_required_documentation(tmp_path) -> None:
    """Analytics routes expose summary, description, and example responses in OpenAPI."""

    app = create_app(tmp_path / "openapi.sqlite3")

    with TestClient(app) as client:
        spec = client.get("/openapi.json").json()

    operations = [
        ("/analytics/daily-trends", "get"),
        ("/analytics/average-mood", "get"),
        ("/analytics/mood-distribution", "get"),
    ]

    for path, method in operations:
        operation = spec["paths"][path][method]
        assert operation.get("summary")
        assert operation.get("description")

        has_example = False
        for response in operation.get("responses", {}).values():
            for media_type in response.get("content", {}).values():
                if "example" in media_type or "examples" in media_type:
                    has_example = True
                    break
            if has_example:
                break
        assert has_example
