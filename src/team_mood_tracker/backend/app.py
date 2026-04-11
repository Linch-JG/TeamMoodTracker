"""FastAPI application for Team Mood Tracker."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status

from team_mood_tracker.backend.api_schemas import ExternalWeatherContext, ServiceHealth
from team_mood_tracker.backend.database import create_mood_entry, initialize_database
from team_mood_tracker.backend.external_context import (
    ExternalContextError,
    fetch_dashboard_weather,
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
        "/dashboard/external-context",
        response_model=ExternalWeatherContext,
        summary="Get external dashboard context",
        description=(
            "Fetches a small weather snapshot from Open-Meteo for the configured team location "
            "so the Streamlit dashboard includes an external API integration."
        ),
        responses={
            status.HTTP_200_OK: {
                "description": "External context fetched successfully.",
                "content": {
                    "application/json": {
                        "example": {
                            "location_name": "Configured Team Location",
                            "temperature_celsius": 12.4,
                            "wind_speed_kph": 9.2,
                            "weather_summary": "Partly cloudy",
                            "observed_at": "2026-04-11T13:00:00",
                            "source": "Open-Meteo",
                        }
                    }
                },
            },
            status.HTTP_502_BAD_GATEWAY: {
                "description": "The external weather provider was unavailable."
            },
        },
    )
    def get_external_dashboard_context() -> ExternalWeatherContext:
        """Return external weather context for the Streamlit dashboard."""

        try:
            return fetch_dashboard_weather()
        except ExternalContextError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(error),
            ) from error

    return mood_app


app = create_app()
