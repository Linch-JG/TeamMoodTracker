"""FastAPI application for Team Mood Tracker."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status

from team_mood_tracker.backend.database import create_mood_entry, initialize_database
from team_mood_tracker.backend.schemas import MoodEntryCreate, MoodEntryRead


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Create a FastAPI app configured for a specific SQLite database."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        initialize_database(database_path)
        yield

    mood_app = FastAPI(
        title="Team Mood Tracker API",
        description="API for submitting team mood entries.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @mood_app.post(
        "/mood-entries",
        response_model=MoodEntryRead,
        status_code=status.HTTP_201_CREATED,
        summary="Submit a mood entry",
        description=(
            "Stores one mood entry with a user name, mood label, numeric rating, "
            "and optional comment. Authentication is intentionally out of scope."
        ),
        responses={
            status.HTTP_201_CREATED: {
                "description": "Mood entry saved to SQLite.",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "user": "Alex",
                            "mood": "happy",
                            "rating": 5,
                            "comment": "Sprint demo went well.",
                            "created_at": "2026-04-10T18:00:00+00:00",
                        }
                    }
                },
            }
        },
    )
    def submit_mood_entry(entry: MoodEntryCreate) -> MoodEntryRead:
        """Store a submitted mood entry."""

        return create_mood_entry(entry, database_path)

    return mood_app


app = create_app()
