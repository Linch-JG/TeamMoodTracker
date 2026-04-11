"""FastAPI application for Team Mood Tracker."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status

from team_mood_tracker.backend.api_schemas import ServiceHealth, WellbeingTip
from team_mood_tracker.backend.database import create_mood_entry, initialize_database
from team_mood_tracker.backend.external_context import (
    ExternalContextError,
    fetch_dashboard_wellbeing_tip,
)
from team_mood_tracker.backend.schemas import MoodEntryCreate, MoodEntryRead


APP_VERSION = "0.1.0"


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Create a FastAPI app configured for a specific SQLite database."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        initialize_database(database_path)
        yield

    mood_app = FastAPI(
        title="Team Mood Tracker API",
        description="API for submitting team mood entries.",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    @mood_app.get(
        "/health",
        response_model=ServiceHealth,
        summary="API health check",
        description="Returns a small health payload so CI and load tests can verify the API is up.",
        responses={
            status.HTTP_200_OK: {
                "description": "API is ready to receive requests.",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "ok",
                            "service": "team-mood-tracker-api",
                            "version": APP_VERSION,
                        }
                    }
                },
            }
        },
    )
    def get_health() -> ServiceHealth:
        """Return a stable health payload for automation."""

        return ServiceHealth(
            status="ok",
            service="team-mood-tracker-api",
            version=APP_VERSION,
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

    @mood_app.get(
        "/dashboard/wellbeing-tip",
        response_model=WellbeingTip,
        summary="Get dashboard well-being tip",
        description=(
            "Fetches a short external reflection quote for the dashboard so the team check-in page "
            "shows a small well-being prompt alongside the mood form."
        ),
        responses={
            status.HTTP_200_OK: {
                "description": "Well-being tip fetched successfully.",
                "content": {
                    "application/json": {
                        "example": {
                            "tip_id": 1,
                            "advice": "It's just a bad day, not a bad life.",
                            "author": "Mary Engelbreit",
                            "source": "ZenQuotes",
                        }
                    }
                },
            },
            status.HTTP_502_BAD_GATEWAY: {
                "description": "The external reflection provider was unavailable."
            },
        },
    )
    def get_dashboard_wellbeing_tip() -> WellbeingTip:
        """Return an external reflection quote for the Streamlit dashboard."""

        try:
            return fetch_dashboard_wellbeing_tip()
        except ExternalContextError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(error),
            ) from error

    return mood_app


app = create_app()
