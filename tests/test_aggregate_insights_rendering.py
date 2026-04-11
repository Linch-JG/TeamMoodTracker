"""Tests for aggregate insights rendering in the analytics frontend module."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_st_for_aggregate(monkeypatch) -> tuple[MagicMock, MagicMock]:
    """Mock Streamlit and the distribution chart helper for aggregate rendering."""

    mock_st = MagicMock()
    columns = [MagicMock(), MagicMock()]
    for column in columns:
        column.__enter__ = MagicMock(return_value=column)
        column.__exit__ = MagicMock(return_value=False)
    mock_st.columns.return_value = columns

    import streamlit
    from team_mood_tracker.frontend import analytics

    for attr in ["subheader", "columns", "date_input", "metric", "info", "error"]:
        monkeypatch.setattr(streamlit, attr, getattr(mock_st, attr))

    mock_render_distribution = MagicMock()
    monkeypatch.setattr(
        analytics,
        "_render_distribution_chart",
        mock_render_distribution,
    )

    return mock_st, mock_render_distribution


def test_render_aggregate_insights_success_path(
    monkeypatch,
    mock_st_for_aggregate,
) -> None:
    """Aggregate insights fetches API data and renders metric and two distributions."""

    mock_st, mock_render_distribution = mock_st_for_aggregate
    mock_st.date_input.side_effect = [
        date(2026, 4, 10),
        date(2026, 4, 11),
        date(2026, 4, 10),
    ]

    average_response = MagicMock()
    average_response.json.return_value = {
        "date_from": "2026-04-10",
        "date_to": "2026-04-11",
        "average_rating": 3.5,
        "total_entries": 2,
    }
    period_distribution_response = MagicMock()
    period_distribution_response.json.return_value = [
        {"mood": "happy", "count": 1},
        {"mood": "neutral", "count": 1},
    ]
    day_distribution_response = MagicMock()
    day_distribution_response.json.return_value = [
        {"mood": "happy", "count": 1},
    ]

    import requests

    get_mock = MagicMock(
        side_effect=[
            average_response,
            period_distribution_response,
            day_distribution_response,
        ]
    )
    monkeypatch.setattr(requests, "get", get_mock)

    from team_mood_tracker.frontend import analytics

    analytics.render_aggregate_insights()

    assert get_mock.call_count == 3
    mock_st.metric.assert_called_once()
    assert mock_render_distribution.call_count == 2


def test_render_aggregate_insights_handles_request_error(
    monkeypatch,
    mock_st_for_aggregate,
) -> None:
    """Aggregate insights surfaces API failures through Streamlit error state."""

    mock_st, _ = mock_st_for_aggregate
    mock_st.date_input.side_effect = [
        date(2026, 4, 10),
        date(2026, 4, 11),
        date(2026, 4, 10),
    ]

    import requests

    monkeypatch.setattr(
        requests,
        "get",
        MagicMock(side_effect=requests.RequestException("boom")),
    )

    from team_mood_tracker.frontend import analytics

    analytics.render_aggregate_insights()

    mock_st.error.assert_called_once()
