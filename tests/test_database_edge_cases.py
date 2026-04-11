"""Additional backend edge case tests to improve coverage."""

from __future__ import annotations

from pathlib import Path

from team_mood_tracker.backend.database import get_database_path, DATABASE_PATH_ENV


def test_get_database_path_uses_env(monkeypatch) -> None:
    """get_database_path uses environment variable when set."""

    monkeypatch.setenv(DATABASE_PATH_ENV, "/custom/path/db.sqlite3")

    result = get_database_path()

    assert result == Path("/custom/path/db.sqlite3")


def test_get_database_path_uses_default(monkeypatch) -> None:
    """get_database_path uses default when environment variable not set."""

    monkeypatch.delenv(DATABASE_PATH_ENV, raising=False)

    result = get_database_path()

    assert result == Path("data/team_mood_tracker.sqlite3")
