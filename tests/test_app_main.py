"""Tests for main Streamlit app with mocked components."""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_st_and_components(
    monkeypatch,
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock]:
    """Mock Streamlit and component rendering functions."""

    mock_st = MagicMock()
    mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]
    for tab in mock_st.tabs.return_value:
        tab.__enter__ = MagicMock(return_value=tab)
        tab.__exit__ = MagicMock(return_value=False)

    mock_render_wellbeing = MagicMock()
    mock_render_submission = MagicMock()
    mock_render_history = MagicMock()
    mock_render_trends = MagicMock()
    mock_render_aggregate = MagicMock()

    import streamlit

    for attr in ["set_page_config", "title", "write", "divider", "tabs"]:
        monkeypatch.setattr(streamlit, attr, getattr(mock_st, attr))

    from team_mood_tracker.frontend import (
        dashboard_context,
        submission_form,
        history_view,
        analytics,
    )

    monkeypatch.setattr(
        dashboard_context, "render_wellbeing_tip_panel", mock_render_wellbeing
    )
    monkeypatch.setattr(
        submission_form, "render_submission_form", mock_render_submission
    )
    monkeypatch.setattr(history_view, "render_history_view", mock_render_history)
    monkeypatch.setattr(analytics, "render_daily_trends", mock_render_trends)
    monkeypatch.setattr(analytics, "render_aggregate_insights", mock_render_aggregate)

    return (
        mock_st,
        mock_render_wellbeing,
        mock_render_submission,
        mock_render_history,
        mock_render_trends,
        mock_render_aggregate,
    )


def test_main_renders_all_components(mock_st_and_components) -> None:
    """main function renders all UI components."""

    (
        mock_st,
        mock_wellbeing,
        mock_submission,
        mock_history,
        mock_trends,
        mock_aggregate,
    ) = mock_st_and_components

    from team_mood_tracker.frontend import app

    app.main()

    mock_st.set_page_config.assert_called_once()
    mock_st.title.assert_called_once()
    mock_st.write.assert_called_once()
    mock_wellbeing.assert_called_once()
    mock_st.divider.assert_called_once()
    mock_st.tabs.assert_called_once()
    mock_submission.assert_called_once()
    mock_history.assert_called_once()
    mock_trends.assert_called_once()
    mock_aggregate.assert_called_once()
