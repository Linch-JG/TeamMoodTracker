"""SQLite persistence for mood submissions."""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

from team_mood_tracker.backend.schemas import (
    AverageMoodInsight,
    DailyTrend,
    MoodEntryCreate,
    MoodDistribution,
    MoodEntryRead,
    MoodEntryUpdate,
)

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
        inserted_entry_id = cursor.lastrowid

    if inserted_entry_id is None:
        raise RuntimeError("SQLite did not return an inserted row id.")

    return MoodEntryRead(
        id=inserted_entry_id,
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


def get_average_mood_insight(
    database_path: str | Path | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> AverageMoodInsight:
    """Return average mood statistics for an optional inclusive date range."""

    initialize_database(database_path)

    query = "SELECT AVG(rating) AS average_rating, COUNT(*) AS total_entries FROM mood_entries"
    conditions: list[str] = []
    params: list[str] = []

    if date_from is not None:
        conditions.append("substr(created_at, 1, 10) >= ?")
        params.append(date_from.isoformat())
    if date_to is not None:
        conditions.append("substr(created_at, 1, 10) <= ?")
        params.append(date_to.isoformat())
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    with connect(database_path) as connection:
        row = connection.execute(query, params).fetchone()

    average_rating: float | None
    if row is None or row["average_rating"] is None:
        average_rating = None
    else:
        average_rating = float(row["average_rating"])

    total_entries = 0 if row is None else int(row["total_entries"])
    return AverageMoodInsight(
        date_from=date_from.isoformat() if date_from is not None else None,
        date_to=date_to.isoformat() if date_to is not None else None,
        average_rating=average_rating,
        total_entries=total_entries,
    )


def get_mood_distribution(
    database_path: str | Path | None = None,
    target_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[MoodDistribution]:
    """Return mood distribution counts with optional date filters."""

    initialize_database(database_path)

    query = "SELECT mood, COUNT(*) AS count FROM mood_entries"
    conditions: list[str] = []
    params: list[str] = []

    if target_date is not None:
        conditions.append("substr(created_at, 1, 10) = ?")
        params.append(target_date.isoformat())
    else:
        if date_from is not None:
            conditions.append("substr(created_at, 1, 10) >= ?")
            params.append(date_from.isoformat())
        if date_to is not None:
            conditions.append("substr(created_at, 1, 10) <= ?")
            params.append(date_to.isoformat())

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY mood ORDER BY count DESC, mood ASC"

    with connect(database_path) as connection:
        rows = connection.execute(query, params).fetchall()

    return [MoodDistribution(mood=row["mood"], count=row["count"]) for row in rows]


class MoodEntryNotFoundError(Exception):
    """Raised when a mood entry with the specified ID does not exist."""

    pass


def list_mood_entries(
    database_path: str | Path | None = None,
    user: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = "date",
    order: str = "desc",
) -> list[MoodEntryRead]:
    """List mood entries with optional filtering and sorting."""

    initialize_database(database_path)

    query = "SELECT id, user, mood, rating, comment, created_at FROM mood_entries"
    conditions = []
    params = []

    if user:
        conditions.append("user = ?")
        params.append(user)

    if date_from:
        conditions.append("substr(created_at, 1, 10) >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("substr(created_at, 1, 10) <= ?")
        params.append(date_to)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if sort_by == "rating":
        query += f" ORDER BY rating {order.upper()}"
    else:
        query += f" ORDER BY created_at {order.upper()}"

    with connect(database_path) as connection:
        cursor = connection.execute(query, params)
        return [
            MoodEntryRead(
                id=row["id"],
                user=row["user"],
                mood=row["mood"],
                rating=row["rating"],
                comment=row["comment"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in cursor.fetchall()
        ]


def get_mood_entry_by_id(
    entry_id: int,
    database_path: str | Path | None = None,
) -> MoodEntryRead:
    """Fetch a single mood entry by ID."""

    initialize_database(database_path)

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            SELECT id, user, mood, rating, comment, created_at
            FROM mood_entries
            WHERE id = ?
            """,
            (entry_id,),
        )
        row = cursor.fetchone()

    if row is None:
        raise MoodEntryNotFoundError(f"Mood entry with ID {entry_id} not found")

    return MoodEntryRead(
        id=row["id"],
        user=row["user"],
        mood=row["mood"],
        rating=row["rating"],
        comment=row["comment"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def update_mood_entry(
    entry_id: int,
    update: MoodEntryUpdate,
    database_path: str | Path | None = None,
) -> MoodEntryRead:
    """Update an existing mood entry."""

    initialize_database(database_path)

    existing = get_mood_entry_by_id(entry_id, database_path)

    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    set_clauses = []
    params = []
    for field, value in update_data.items():
        set_clauses.append(f"{field} = ?")
        params.append(value)

    params.append(entry_id)

    with connect(database_path) as connection:
        connection.execute(
            f"UPDATE mood_entries SET {', '.join(set_clauses)} WHERE id = ?",  # nosec B608
            params,
        )

    return get_mood_entry_by_id(entry_id, database_path)


def delete_mood_entry(
    entry_id: int,
    database_path: str | Path | None = None,
) -> None:
    """Delete a mood entry by ID."""

    initialize_database(database_path)

    get_mood_entry_by_id(entry_id, database_path)

    with connect(database_path) as connection:
        connection.execute(
            "DELETE FROM mood_entries WHERE id = ?",
            (entry_id,),
        )
