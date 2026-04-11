"""Streamlit helpers for the external dashboard context widget."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


API_BASE_URL_ENV = "TEAM_MOOD_API_URL"
DEFAULT_API_BASE_URL = "http://localhost:8000"


def fetch_dashboard_external_context(
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Fetch external dashboard context data from the FastAPI backend."""

    base_url = api_base_url or os.getenv(API_BASE_URL_ENV, DEFAULT_API_BASE_URL)
    response = requests.get(
        f"{base_url.rstrip('/')}/dashboard/external-context",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def render_external_context_panel() -> None:
    """Render a small dashboard widget backed by an external API."""

    with st.container(border=True):
        st.subheader("External Context")
        st.caption(
            "Current weather from Open-Meteo for the configured team location. "
            "This satisfies the course external API requirement without adding authentication."
        )

        try:
            snapshot = fetch_dashboard_external_context()
        except requests.HTTPError as error:
            detail = error.response.text if error.response is not None else str(error)
            st.warning(f"External context is unavailable right now: {detail}")
            return
        except requests.RequestException as error:
            st.warning(f"Cannot load external context: {error}")
            return

        st.write(f"Configured location: **{snapshot['location_name']}**")
        temperature, weather, wind = st.columns(3)
        temperature.metric("Temperature", f"{snapshot['temperature_celsius']:.1f} C")
        weather.metric("Conditions", snapshot["weather_summary"])
        wind.metric("Wind", f"{snapshot['wind_speed_kph']:.1f} km/h")
        st.caption(f"Observed at {snapshot['observed_at']}. Source: {snapshot['source']}.")
