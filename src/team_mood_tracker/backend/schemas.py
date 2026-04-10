"""Pydantic schemas for mood submission."""

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

    id: int = Field(description="Database identifier for the stored mood entry.", examples=[1])
    created_at: datetime = Field(
        description="UTC timestamp recorded when the mood entry was submitted.",
        examples=["2026-04-10T18:00:00+00:00"],
    )
