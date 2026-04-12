"""FastAPI application for Team Mood Tracker."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, status

from team_mood_tracker.backend.api_schemas import ServiceHealth, WellbeingTip
from team_mood_tracker.backend.database import (
    create_mood_entry,
    delete_mood_entry,
    get_average_mood_insight,
    get_daily_trends,
    get_mood_distribution,
    get_mood_entry_by_id,
    initialize_database,
    list_mood_entries,
    MoodEntryNotFoundError,
    update_mood_entry,
)
from team_mood_tracker.backend.external_context import (
    ExternalContextError,
    fetch_dashboard_wellbeing_tip,
)
from team_mood_tracker.backend.schemas import (
    AverageMoodInsight,
    DailyTrend,
    MoodDistribution,
    MoodEntryCreate,
    MoodEntryRead,
    MoodEntryUpdate,
)

APP_VERSION = "0.1.0"


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Create a FastAPI app configured for a specific SQLite database."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Initialize local storage when the API process starts."""

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
        "/mood-entries",
        response_model=list[MoodEntryRead],
        summary="List mood entries",
        description=(
            "Retrieves a list of mood entries with optional filtering by user and date range. "
            "Results can be sorted by date or rating in ascending or descending order."
        ),
        responses={
            status.HTTP_200_OK: {
                "description": "List of mood entries matching the filter criteria.",
                "content": {
                    "application/json": {
                        "example": [
                            {
                                "id": 1,
                                "user": "Alex",
                                "mood": "happy",
                                "rating": 5,
                                "comment": "Sprint demo went well.",
                                "created_at": "2026-04-10T18:00:00+00:00",
                            },
                            {
                                "id": 2,
                                "user": "Jordan",
                                "mood": "stressed",
                                "rating": 2,
                                "comment": "Multiple deadlines today.",
                                "created_at": "2026-04-10T14:30:00+00:00",
                            },
                        ]
                    }
                },
            }
        },
    )
    def list_mood_entries_endpoint(
        user: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        sort_by: str = "date",
        order: str = "desc",
    ) -> list[MoodEntryRead]:
        """List mood entries with optional filtering and sorting."""

        return list_mood_entries(
            database_path=database_path,
            user=user,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
        )

    @mood_app.get(
        "/mood-entries/{entry_id}",
        response_model=MoodEntryRead,
        summary="Get a single mood entry",
        description="Retrieves a specific mood entry by its unique identifier.",
        responses={
            status.HTTP_200_OK: {
                "description": "Mood entry retrieved successfully.",
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
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Mood entry with the specified ID does not exist."
            },
        },
    )
    def get_mood_entry_endpoint(entry_id: int) -> MoodEntryRead:
        """Retrieve a specific mood entry by ID."""

        try:
            return get_mood_entry_by_id(entry_id, database_path)
        except MoodEntryNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

    @mood_app.put(
        "/mood-entries/{entry_id}",
        response_model=MoodEntryRead,
        summary="Update a mood entry",
        description=(
            "Updates one or more fields of an existing mood entry. "
            "Only the fields provided in the request body will be updated."
        ),
        responses={
            status.HTTP_200_OK: {
                "description": "Mood entry updated successfully.",
                "content": {
                    "application/json": {
                        "example": {
                            "id": 1,
                            "user": "Alex",
                            "mood": "neutral",
                            "rating": 3,
                            "comment": "Feeling better after lunch.",
                            "created_at": "2026-04-10T18:00:00+00:00",
                        }
                    }
                },
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Mood entry with the specified ID does not exist."
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Invalid update data provided."
            },
        },
    )
    def update_mood_entry_endpoint(
        entry_id: int,
        update: MoodEntryUpdate,
    ) -> MoodEntryRead:
        """Update an existing mood entry."""

        try:
            return update_mood_entry(entry_id, update, database_path)
        except MoodEntryNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

    @mood_app.delete(
        "/mood-entries/{entry_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete a mood entry",
        description="Permanently removes a mood entry from the database.",
        responses={
            status.HTTP_204_NO_CONTENT: {
                "description": "Mood entry deleted successfully."
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Mood entry with the specified ID does not exist.",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "Mood entry with ID 404 not found",
                        }
                    }
                },
            },
        },
    )
    def delete_mood_entry_endpoint(entry_id: int) -> None:
        """Delete a mood entry by ID."""

        try:
            delete_mood_entry(entry_id, database_path)
        except MoodEntryNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error

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

    @mood_app.get(
        "/analytics/daily-trends",
        response_model=list[DailyTrend],
        summary="Get daily mood trends",
        description="Returns the average mood rating per day.",
        responses={
            status.HTTP_200_OK: {
                "description": "Daily average mood values ordered by date.",
                "content": {
                    "application/json": {
                        "example": [
                            {"date": "2026-04-10", "average_rating": 3.5},
                            {"date": "2026-04-11", "average_rating": 4.0},
                        ]
                    }
                },
            }
        },
    )
    def get_daily_analytics() -> list[DailyTrend]:
        """Return the average mood rating per day."""
        return get_daily_trends(database_path)

    @mood_app.get(
        "/analytics/average-mood",
        response_model=AverageMoodInsight,
        summary="Get average mood for a period",
        description=(
            "Returns aggregate average mood rating for an optional inclusive date range. "
            "When no date range is provided, all stored entries are included."
        ),
        responses={
            status.HTTP_200_OK: {
                "description": "Average mood aggregate for the selected period.",
                "content": {
                    "application/json": {
                        "example": {
                            "date_from": "2026-04-01",
                            "date_to": "2026-04-14",
                            "average_rating": 3.8,
                            "total_entries": 24,
                        }
                    }
                },
            }
        },
    )
    def get_average_mood(
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> AverageMoodInsight:
        """Return aggregate average mood statistics for a selected period."""

        return get_average_mood_insight(
            database_path=database_path,
            date_from=date_from,
            date_to=date_to,
        )

    @mood_app.get(
        "/analytics/mood-distribution",
        response_model=list[MoodDistribution],
        summary="Get mood distribution",
        description=(
            "Returns mood bucket counts. Use `target_date` for a single-day view, or use "
            "`date_from` and `date_to` for a selected period. Without filters, all entries are used."
        ),
        responses={
            status.HTTP_200_OK: {
                "description": "Mood distribution buckets ordered by count.",
                "content": {
                    "application/json": {
                        "example": [
                            {"mood": "happy", "count": 8},
                            {"mood": "neutral", "count": 6},
                            {"mood": "stressed", "count": 4},
                        ]
                    }
                },
            }
        },
    )
    def get_distribution_analytics(
        target_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[MoodDistribution]:
        """Return mood distribution counts for daily or period insights."""

        return get_mood_distribution(
            database_path=database_path,
            target_date=target_date,
            date_from=date_from,
            date_to=date_to,
        )

    return mood_app


app = create_app()
