"""Main Streamlit entry point for Team Mood Tracker."""

from __future__ import annotations

import streamlit as st

from team_mood_tracker.frontend.dashboard_context import render_wellbeing_tip_panel
from team_mood_tracker.frontend.submission_form import render_submission_form
from team_mood_tracker.frontend.analytics import render_daily_trends


def main() -> None:
    """Run the Team Mood Tracker dashboard."""

    st.set_page_config(page_title="Team Mood Tracker")
    st.title("Team Mood Tracker")
    st.write("Share how today feels so the team can notice pressure early.")
    render_wellbeing_tip_panel()
    st.divider()
    render_submission_form(show_heading=False)
    st.divider()
    render_daily_trends()


if __name__ == "__main__":
    main()
