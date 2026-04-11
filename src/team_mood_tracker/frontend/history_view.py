"""Mood history management interface for Streamlit."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE_URL_ENV = "TEAM_MOOD_API_URL"
DEFAULT_API_BASE_URL = "http://localhost:8000"


def get_api_base_url(api_base_url: str | None = None) -> str:
    """Get the API base URL from parameter or environment."""

    base_url = api_base_url or os.getenv(API_BASE_URL_ENV, DEFAULT_API_BASE_URL)
    return base_url.rstrip("/") + "/"


def fetch_mood_entries(
    api_base_url: str | None = None,
    user: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = "date",
    order: str = "desc",
) -> list[dict[str, Any]]:
    """Fetch mood entries from the API with optional filtering and sorting."""

    base_url = get_api_base_url(api_base_url)
    params = {}
    if user:
        params["user"] = user
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    params["sort_by"] = sort_by
    params["order"] = order

    response = requests.get(
        f"{base_url}mood-entries",
        params=params,
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def update_mood_entry(
    entry_id: int,
    update_data: dict[str, Any],
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Update a mood entry via the API."""

    base_url = get_api_base_url(api_base_url)
    response = requests.put(
        f"{base_url}mood-entries/{entry_id}",
        json=update_data,
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def delete_mood_entry_api(entry_id: int, api_base_url: str | None = None) -> None:
    """Delete a mood entry via the API."""

    base_url = get_api_base_url(api_base_url)
    response = requests.delete(
        f"{base_url}mood-entries/{entry_id}",
        timeout=5,
    )
    response.raise_for_status()


def render_history_view(api_base_url: str | None = None) -> None:
    """Render the mood history management interface."""

    st.header("Mood History")

    with st.expander("Filters and Sorting", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            filter_user = st.text_input(
                "Filter by User",
                value="",
                help="Leave empty to show all users",
            )
            date_from = st.date_input("Date From", value=None)

        with col2:
            sort_by = st.selectbox("Sort By", ["date", "rating"], index=0)
            date_to = st.date_input("Date To", value=None)

        order = st.radio("Order", ["desc", "asc"], index=0, horizontal=True)

    if st.button("Refresh", type="primary"):
        st.rerun()

    try:
        entries = fetch_mood_entries(
            api_base_url,
            user=filter_user if filter_user else None,
            date_from=str(date_from) if date_from else None,
            date_to=str(date_to) if date_to else None,
            sort_by=sort_by,
            order=order,
        )

        if not entries:
            st.info("No mood entries found.")
            return

        st.write(f"Showing {len(entries)} entries:")

        for entry in entries:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    created_at = entry["created_at"].split("T")[0]
                    st.write(
                        f"**{entry['user']}** - {entry['mood']} "
                        f"(Rating: {entry['rating']}/5) - {created_at}"
                    )
                    if entry.get("comment"):
                        st.write(f"_{entry['comment']}_")

                with col2:
                    if st.button("Edit", key=f"edit_{entry['id']}"):
                        st.session_state[f"editing_{entry['id']}"] = True
                        st.rerun()

                with col3:
                    if st.button("Delete", key=f"delete_{entry['id']}"):
                        st.session_state[f"confirm_delete_{entry['id']}"] = True
                        st.rerun()

                if st.session_state.get(f"editing_{entry['id']}", False):
                    render_edit_form(entry, api_base_url)

                if st.session_state.get(f"confirm_delete_{entry['id']}", False):
                    render_delete_confirmation(entry, api_base_url)

                st.divider()

    except requests.exceptions.RequestException as error:
        st.error(f"Failed to fetch mood entries: {error}")


def render_edit_form(entry: dict[str, Any], api_base_url: str | None = None) -> None:
    """Render the edit form for a mood entry."""

    st.subheader(f"Edit Entry #{entry['id']}")

    with st.form(key=f"edit_form_{entry['id']}"):
        updated_user = st.text_input("User", value=entry["user"])
        updated_mood = st.text_input("Mood", value=entry["mood"])
        updated_rating = st.slider("Rating", 1, 5, entry["rating"])
        updated_comment = st.text_area(
            "Comment",
            value=entry.get("comment", ""),
            max_chars=500,
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Save Changes", type="primary")
        with col2:
            cancel = st.form_submit_button("Cancel")

        if submit:
            try:
                update_data = {
                    "user": updated_user,
                    "mood": updated_mood,
                    "rating": updated_rating,
                    "comment": updated_comment if updated_comment else None,
                }
                update_mood_entry(entry["id"], update_data, api_base_url)
                st.success("Entry updated successfully!")
                st.session_state[f"editing_{entry['id']}"] = False
                st.rerun()
            except requests.exceptions.RequestException as error:
                st.error(f"Failed to update entry: {error}")

        if cancel:
            st.session_state[f"editing_{entry['id']}"] = False
            st.rerun()


def render_delete_confirmation(
    entry: dict[str, Any], api_base_url: str | None = None
) -> None:
    """Render delete confirmation dialog."""

    st.warning(
        f"Are you sure you want to delete this entry by {entry['user']} "
        f"({entry['mood']}, rating {entry['rating']})?"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm Delete", key=f"confirm_{entry['id']}", type="primary"):
            try:
                delete_mood_entry_api(entry["id"], api_base_url)
                st.success("Entry deleted successfully!")
                st.session_state[f"confirm_delete_{entry['id']}"] = False
                st.rerun()
            except requests.exceptions.RequestException as error:
                st.error(f"Failed to delete entry: {error}")

    with col2:
        if st.button("Cancel Delete", key=f"cancel_{entry['id']}"):
            st.session_state[f"confirm_delete_{entry['id']}"] = False
            st.rerun()
