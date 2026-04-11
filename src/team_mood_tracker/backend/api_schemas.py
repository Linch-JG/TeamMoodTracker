"""Additional API schemas owned by the dashboard and CI support work."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ServiceHealth(BaseModel):
    """Health response used by CI and performance checks."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "service": "team-mood-tracker-api",
                "version": "0.1.0",
            }
        }
    )

    status: Literal["ok"] = Field(description="Health status for the API service.")
    service: str = Field(description="Stable service identifier for automation.")
    version: str = Field(description="Application version reported by the API.")


class WellbeingTip(BaseModel):
    """External well-being advice shown on the dashboard."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tip_id": 1,
                "advice": "It's just a bad day, not a bad life.",
                "author": "Mary Engelbreit",
                "source": "ZenQuotes",
            }
        }
    )

    tip_id: int = Field(
        description="Provider identifier for the advice item.",
        examples=[117],
    )
    advice: str = Field(
        description="Short well-being or reflection advice returned by the provider.",
        examples=["It's just a bad day, not a bad life."],
    )
    author: str = Field(
        description="Author associated with the tip or quote when provided by the source API.",
        examples=["Mary Engelbreit"],
    )
    source: str = Field(
        description="External provider used for the dashboard widget.",
        examples=["ZenQuotes"],
    )
