"""Analytics views for trend and aggregate insight visualizations."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st

API_BASE_URL_ENV = "TEAM_MOOD_API_URL"
DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


def _api_url(path: str) -> str:
    """Build a normalized API URL for analytics requests."""

    base_url = os.getenv(API_BASE_URL_ENV, DEFAULT_API_BASE_URL).rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


def _format_period_params(
    date_from: date | None,
    date_to: date | None,
) -> dict[str, str]:
    """Convert optional date boundaries into API query parameters."""

    params: dict[str, str] = {}
    if date_from is not None:
        params["date_from"] = date_from.isoformat()
    if date_to is not None:
        params["date_to"] = date_to.isoformat()
    return params


def _render_distribution_chart(
    data: list[dict[str, Any]],
    title: str,
) -> None:
    """Render one mood distribution barplot from API response data."""

    if not data:
        st.info(f"{title}: no entries for the selected filter.")
        return

    distribution_df = pd.DataFrame(data)
    chart = (
        alt.Chart(distribution_df)
        .mark_bar()
        .encode(
            x=alt.X("mood:N", title="Mood"),
            y=alt.Y("count:Q", title="Entries"),
            tooltip=["mood", "count"],
        )
        .properties(height=280, title=title)
    )
    st.altair_chart(chart, use_container_width=True)


def render_daily_trends() -> None:
    """Render a line chart of the daily average mood score."""

    st.header("Daily Mood Trends")
    try:
        response = requests.get(_api_url("/analytics/daily-trends"), timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            st.info("No mood entries yet.")
            return

        trends_df = pd.DataFrame(data)
        trends_df["date"] = pd.to_datetime(trends_df["date"])
        chart = (
            alt.Chart(trends_df)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                    "date:T",
                    title="Date",
                    axis=alt.Axis(format="%Y-%m-%d", labelAngle=-35),
                ),
                y=alt.Y(
                    "average_rating:Q",
                    title="Average Rating",
                    scale=alt.Scale(domain=[1, 5]),
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                    alt.Tooltip(
                        "average_rating:Q", title="Average rating", format=".2f"
                    ),
                ],
            )
            .properties(width=600, height=300)
        )

        st.altair_chart(chart, use_container_width=True)

    except requests.RequestException as error:
        st.error(f"Could not load trends data: {error}")


def render_aggregate_insights() -> None:
    """Render average-mood aggregates and distribution barplots."""

    st.subheader("Aggregate Insights")

    period_col1, period_col2 = st.columns(2)
    with period_col1:
        date_from = st.date_input("Period start", value=None, key="insight_date_from")
    with period_col2:
        date_to = st.date_input("Period end", value=None, key="insight_date_to")

    period_params = _format_period_params(date_from, date_to)

    try:
        average_response = requests.get(
            _api_url("/analytics/average-mood"),
            params=period_params,
            timeout=5,
        )
        average_response.raise_for_status()
        average_data = average_response.json()

        if average_data["average_rating"] is None:
            st.info(
                "Average mood is unavailable because no entries match the selected period."
            )
        else:
            st.metric(
                label="Average mood rating",
                value=f"{average_data['average_rating']:.2f}/5",
                help=f"Calculated from {average_data['total_entries']} entries.",
            )

        period_distribution_response = requests.get(
            _api_url("/analytics/mood-distribution"),
            params=period_params,
            timeout=5,
        )
        period_distribution_response.raise_for_status()
        period_distribution = period_distribution_response.json()
        _render_distribution_chart(
            period_distribution,
            title="Mood Distribution (Selected Period)",
        )

        selected_day = st.date_input(
            "Distribution day",
            value=date.today(),
            key="insight_distribution_day",
        )
        day_response = requests.get(
            _api_url("/analytics/mood-distribution"),
            params={"target_date": selected_day.isoformat()},
            timeout=5,
        )
        day_response.raise_for_status()
        day_distribution = day_response.json()
        _render_distribution_chart(
            day_distribution,
            title=f"Mood Distribution ({selected_day.isoformat()})",
        )

    except requests.RequestException as error:
        st.error(f"Could not load aggregate insights: {error}")
