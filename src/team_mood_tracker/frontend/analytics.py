import requests
import streamlit as st
import pandas as pd
import altair as alt

API_URL = "http://127.0.0.1:8000"


def render_daily_trends():
    st.header("Daily Mood Trends")
    try:
        response = requests.get(f"{API_URL}/analytics/daily-trends", timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            st.info("No mood entries yet.")
            return

        df = pd.DataFrame(data)
        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y(
                    "average_rating:Q",
                    title="Average Rating",
                    scale=alt.Scale(domain=[1, 5]),
                ),
                tooltip=["date", "average_rating"],
            )
            .properties(width=600, height=300)
        )

        st.altair_chart(chart, use_container_width=True)

    except requests.RequestException as e:
        st.error(f"Could not load trends data: {e}")
