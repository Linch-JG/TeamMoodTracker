"""Pydantic schemas for Team Mood Tracker request and response payloads."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MoodEntryCreate(BaseModel):
    """Request body for submitting a mood entry."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user": "Alex",
                    "mood": "happy",
                    "rating": 5,
                    "comment": "Sprint demo went well.",
                }
            ]
        }
    )

    user: str = Field(
        min_length=1,
        max_length=80,
        description="Name used to differentiate users without authentication.",
        examples=["Alex"],
    )
    mood: str = Field(
        min_length=1,
        max_length=40,
        description="Mood label selected by the user, for example happy or stressed.",
        examples=["happy"],
    )
    rating: int = Field(
        ge=1,
        le=5,
        description="Mood intensity on a 1 to 5 scale.",
        examples=[5],
    )
    comment: str | None = Field(
        default=None,
        max_length=500,
        description="Optional free-text context for the submitted mood.",
        examples=["Sprint demo went well."],
    )


class MoodEntryRead(MoodEntryCreate):
    """Response body returned after a mood entry is stored."""

    id: int = Field(
        description="Database identifier for the stored mood entry.", examples=[1]
    )
    created_at: datetime = Field(
        description="UTC timestamp recorded when the mood entry was submitted.",
        examples=["2026-04-10T18:00:00+00:00"],
    )


class MoodEntryUpdate(BaseModel):
    """Request body for updating a mood entry with optional fields."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "mood": "neutral",
                    "rating": 3,
                    "comment": "Feeling better after lunch.",
                }
            ]
        }
    )

    user: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
        description="Updated user name.",
        examples=["Alex"],
    )
    mood: str | None = Field(
        default=None,
        min_length=1,
        max_length=40,
        description="Updated mood label.",
        examples=["neutral"],
    )
    rating: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Updated mood intensity rating.",
        examples=[3],
    )
    comment: str | None = Field(
        default=None,
        max_length=500,
        description="Updated comment.",
        examples=["Feeling better after lunch."],
    )


class DailyTrend(BaseModel):
    """Daily average mood trend."""

    date: str = Field(
        description="Calendar date in YYYY-MM-DD format.",
        examples=["2026-04-10"],
    )
    average_rating: float = Field(
        description="Average mood rating for the given date.",
        examples=[3.5],
    )


class MoodDistribution(BaseModel):
    """Mood distribution count."""

    mood: str = Field(
        description="Mood label in the aggregated bucket.",
        examples=["happy"],
    )
    count: int = Field(
        description="Number of entries that match this mood label.",
        examples=[8],
    )


class AverageMoodInsight(BaseModel):
    """Aggregated average mood score for a selected date period."""

    date_from: str | None = Field(
        default=None,
        description="Inclusive period start in YYYY-MM-DD format when filtering is used.",
        examples=["2026-04-01"],
    )
    date_to: str | None = Field(
        default=None,
        description="Inclusive period end in YYYY-MM-DD format when filtering is used.",
        examples=["2026-04-14"],
    )
    average_rating: float | None = Field(
        default=None,
        description="Average mood rating in the selected period. Null when no entries match.",
        examples=[3.8],
    )
    total_entries: int = Field(
        description="Number of mood entries included in the aggregate.",
        examples=[24],
    )
