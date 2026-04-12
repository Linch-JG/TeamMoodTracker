"""Streamlit form for submitting team mood entries."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE_URL_ENV = "TEAM_MOOD_API_URL"
DEFAULT_API_BASE_URL = "http://localhost:8000"
MOOD_OPTIONS = ("happy", "neutral", "stressed", "tired", "excited")


def get_api_base_url(api_base_url: str | None = None) -> str:
    """Resolve and normalize the API base URL for frontend requests."""

    resolved_base_url = api_base_url
    if resolved_base_url is None:
        resolved_base_url = os.getenv(API_BASE_URL_ENV, DEFAULT_API_BASE_URL)
    return resolved_base_url.rstrip("/")


def submit_mood_entry(
    payload: dict[str, Any],
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Submit a mood entry payload to the FastAPI backend."""

    base_url = get_api_base_url(api_base_url)
    response = requests.post(
        f"{base_url}/mood-entries",
        json=payload,
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def _format_submission_error(error: requests.RequestException) -> str:
    """Return a user-facing message for a failed mood submission request."""

    if isinstance(error, requests.HTTPError) and error.response is not None:
        return f"Submission failed: {error.response.text}"
    return f"Cannot reach the mood API: {error}"


def _show_submission_result(payload: dict[str, Any]) -> None:
    """Submit payload and surface success or error in Streamlit."""

    try:
        saved_entry = submit_mood_entry(payload)
    except requests.RequestException as error:
        st.error(_format_submission_error(error))
        return
    st.success(f"Mood entry #{saved_entry['id']} saved.")


def render_submission_form(show_heading: bool = True) -> None:
    """Render the Streamlit mood submission form."""

    if show_heading:
        st.title("Team Mood Tracker")
        st.write("Share how today feels so the team can notice pressure early.")

    with st.form("mood-submission-form", clear_on_submit=True):
        user = st.text_input("Your name")
        mood = st.selectbox("Mood", MOOD_OPTIONS)
        rating = st.slider("Rating", min_value=1, max_value=5, value=3)
        comment = st.text_area("Comment", placeholder="Optional context")
        submitted = st.form_submit_button("Submit mood")

    if not submitted:
        return

    if not user.strip():
        st.error("Enter your name before submitting.")
        return

    payload = {
        "user": user.strip(),
        "mood": mood,
        "rating": rating,
        "comment": comment.strip() or None,
    }
    _show_submission_result(payload)


def main() -> None:
    """Run the Streamlit app."""

    render_submission_form()


if __name__ == "__main__":
    main()
