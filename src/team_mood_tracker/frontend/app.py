"""Main Streamlit entry point for Team Mood Tracker."""

from __future__ import annotations

import streamlit as st

from team_mood_tracker.frontend.dashboard_context import render_external_context_panel
from team_mood_tracker.frontend.submission_form import render_submission_form


def main() -> None:
    """Run the Team Mood Tracker dashboard."""

    st.set_page_config(page_title="Team Mood Tracker")
    st.title("Team Mood Tracker")
    st.write("Share how today feels so the team can notice pressure early.")
    render_external_context_panel()
    st.divider()
    render_submission_form(show_heading=False)


if __name__ == "__main__":
    main()
