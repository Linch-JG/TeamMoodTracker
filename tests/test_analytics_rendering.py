"""Comprehensive Streamlit mock tests for analytics module."""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest
import pandas as pandas_module


@pytest.fixture
def mock_st_and_deps(monkeypatch) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    """Mock Streamlit, requests, pandas, and altair for analytics testing."""

    mock_st = MagicMock()
    mock_requests = MagicMock()
    mock_pd = MagicMock()
    _pandas_dataframe = pandas_module.DataFrame
    mock_pd.DataFrame = MagicMock(side_effect=lambda data: _pandas_dataframe(data))
    mock_alt = MagicMock()

    mock_chart = MagicMock()
    mock_chart.mark_line.return_value = mock_chart
    mock_chart.encode.return_value = mock_chart
    mock_chart.properties.return_value = mock_chart
    mock_alt.Chart.return_value = mock_chart
    mock_alt.X = MagicMock()
    mock_alt.Y = MagicMock()
    mock_alt.Scale = MagicMock()

    import streamlit
    import requests
    import pandas
    import altair

    for attr in ["header", "info", "error", "altair_chart"]:
        monkeypatch.setattr(streamlit, attr, getattr(mock_st, attr))

    monkeypatch.setattr(requests, "get", mock_requests.get)
    monkeypatch.setattr(pandas, "DataFrame", mock_pd.DataFrame)
    monkeypatch.setattr(altair, "Chart", mock_alt.Chart)
    monkeypatch.setattr(altair, "X", mock_alt.X)
    monkeypatch.setattr(altair, "Y", mock_alt.Y)
    monkeypatch.setattr(altair, "Scale", mock_alt.Scale)

    return mock_st, mock_requests, mock_pd, mock_alt


def test_render_daily_trends_with_data(mock_st_and_deps) -> None:
    """render_daily_trends displays chart when data is available."""

    mock_st, mock_requests, mock_pd, mock_alt = mock_st_and_deps

    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"date": "2026-04-10", "average_rating": 4.5},
        {"date": "2026-04-11", "average_rating": 3.8},
    ]
    mock_requests.get.return_value = mock_response

    from team_mood_tracker.frontend import analytics

    analytics.render_daily_trends()

    mock_st.header.assert_called_once_with("Daily Mood Trends")
    mock_requests.get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_pd.DataFrame.assert_called_once()
    mock_alt.Chart.assert_called_once()
    mock_st.altair_chart.assert_called_once()


def test_render_daily_trends_with_no_data(mock_st_and_deps) -> None:
    """render_daily_trends shows info message when no data available."""

    mock_st, mock_requests, mock_pd, mock_alt = mock_st_and_deps

    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_requests.get.return_value = mock_response

    from team_mood_tracker.frontend import analytics

    analytics.render_daily_trends()

    mock_st.header.assert_called_once()
    mock_st.info.assert_called_once_with("No mood entries yet.")


def test_render_daily_trends_with_api_error(mock_st_and_deps) -> None:
    """render_daily_trends handles API errors gracefully."""

    mock_st, mock_requests, mock_pd, mock_alt = mock_st_and_deps

    import requests

    mock_requests.get.side_effect = requests.RequestException("Connection failed")

    from team_mood_tracker.frontend import analytics

    analytics.render_daily_trends()

    mock_st.header.assert_called_once()
    mock_st.error.assert_called_once()
