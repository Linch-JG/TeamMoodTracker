"""Streamlit helpers for the external well-being widget."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE_URL_ENV = "TEAM_MOOD_API_URL"
DEFAULT_API_BASE_URL = "http://localhost:8000"


def get_api_base_url(api_base_url: str | None = None) -> str:
    """Resolve and normalize API base URL for dashboard context calls."""

    resolved_base_url = api_base_url
    if resolved_base_url is None:
        resolved_base_url = os.getenv(API_BASE_URL_ENV, DEFAULT_API_BASE_URL)
    return resolved_base_url.rstrip("/")


def fetch_dashboard_wellbeing_tip(
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Fetch the external well-being tip from the FastAPI backend."""

    base_url = get_api_base_url(api_base_url)
    response = requests.get(
        f"{base_url}/dashboard/wellbeing-tip",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def render_wellbeing_tip_panel() -> None:
    """Render a small dashboard widget backed by an external reflection API."""

    with st.container(border=True):
        st.subheader("Well-being Tip")
        st.caption("A short reflection quote for today's check-in.")

        try:
            snapshot = fetch_dashboard_wellbeing_tip()
        except requests.HTTPError as error:
            detail = error.response.text if error.response is not None else str(error)
            st.warning(f"Well-being tip is unavailable right now: {detail}")
            return
        except requests.RequestException as error:
            st.warning(f"Cannot load the well-being tip: {error}")
            return

        st.info(snapshot["advice"])
        st.caption(f"{snapshot['author']} | {snapshot['source']}")
