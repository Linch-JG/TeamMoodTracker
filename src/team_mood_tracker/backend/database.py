"""SQLite persistence for mood submissions."""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from team_mood_tracker.backend.schemas import DailyTrend, MoodEntryCreate, MoodEntryRead

DATABASE_PATH_ENV = "TEAM_MOOD_DATABASE_PATH"
DEFAULT_DATABASE_PATH = Path("data/team_mood_tracker.sqlite3")


def get_database_path() -> Path:
    """Return the configured SQLite database path."""

    return Path(os.getenv(DATABASE_PATH_ENV, str(DEFAULT_DATABASE_PATH))).expanduser()


def connect(database_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection and ensure its parent directory exists."""

    path = Path(database_path) if database_path is not None else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: str | Path | None = None) -> None:
    """Create the mood entry table when it is not present."""

    with connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                mood TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """)


def create_mood_entry(
    entry: MoodEntryCreate,
    database_path: str | Path | None = None,
) -> MoodEntryRead:
    """Persist a mood submission and return the stored entry."""

    initialize_database(database_path)
    created_at = datetime.now(UTC).replace(microsecond=0)

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO mood_entries (user, mood, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry.user,
                entry.mood,
                entry.rating,
                entry.comment,
                created_at.isoformat(),
            ),
        )

    return MoodEntryRead(
        id=int(cursor.lastrowid),
        user=entry.user,
        mood=entry.mood,
        rating=entry.rating,
        comment=entry.comment,
        created_at=created_at,
    )


def get_daily_trends(database_path: str | Path | None = None) -> list[DailyTrend]:
    """Get daily trends (average mood rating per day)."""

    initialize_database(database_path)
    with connect(database_path) as connection:
        cursor = connection.execute("""
            SELECT substr(created_at, 1, 10) as date, AVG(rating) as average_rating
            FROM mood_entries
            GROUP BY date
            ORDER BY date ASC
            """)
        return [
            DailyTrend(date=row["date"], average_rating=row["average_rating"])
            for row in cursor.fetchall()
        ]
