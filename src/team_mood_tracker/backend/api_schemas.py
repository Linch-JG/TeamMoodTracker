"""Additional API schemas owned by the dashboard and CI support work."""

from __future__ import annotations

from datetime import datetime
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


class ExternalWeatherContext(BaseModel):
    """Current external weather snapshot shown on the dashboard."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location_name": "Configured Team Location",
                "temperature_celsius": 12.4,
                "wind_speed_kph": 9.2,
                "weather_summary": "Partly cloudy",
                "observed_at": "2026-04-11T13:00:00",
                "source": "Open-Meteo",
            }
        }
    )

    location_name: str = Field(
        description="Human-friendly label for the configured team location.",
        examples=["Configured Team Location"],
    )
    temperature_celsius: float = Field(
        description="Current air temperature in degrees Celsius.",
        examples=[12.4],
    )
    wind_speed_kph: float = Field(
        description="Current wind speed in kilometers per hour.",
        examples=[9.2],
    )
    weather_summary: str = Field(
        description="Short weather label derived from the provider weather code.",
        examples=["Partly cloudy"],
    )
    observed_at: datetime = Field(
        description="Timestamp reported by the external provider for the weather snapshot.",
        examples=["2026-04-11T13:00:00"],
    )
    source: str = Field(
        description="External provider used for the dashboard widget.",
        examples=["Open-Meteo"],
    )
