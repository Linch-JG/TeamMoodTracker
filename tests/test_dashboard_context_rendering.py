"""Comprehensive tests for dashboard context rendering with mocks."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_st_full(monkeypatch) -> MagicMock:
    """Mock Streamlit completely for dashboard context testing."""

    mock_st = MagicMock()
    mock_st.container.return_value.__enter__ = MagicMock()
    mock_st.container.return_value.__exit__ = MagicMock(return_value=False)

    import streamlit

    for attr in ["container", "subheader", "caption", "warning", "info"]:
        monkeypatch.setattr(streamlit, attr, getattr(mock_st, attr))

    return mock_st


def test_render_wellbeing_tip_panel_displays_tip(mock_st_full, monkeypatch) -> None:
    """render_wellbeing_tip_panel displays tip when API succeeds."""

    from team_mood_tracker.frontend import dashboard_context

    tip_data = {
        "tip_id": 1,
        "advice": "Take a moment to breathe.",
        "author": "Wisdom Master",
        "source": "ZenQuotes",
    }

    monkeypatch.setattr(
        dashboard_context,
        "fetch_dashboard_wellbeing_tip",
        lambda *args, **kwargs: tip_data,
    )

    dashboard_context.render_wellbeing_tip_panel()

    mock_st_full.container.assert_called_once()
    mock_st_full.subheader.assert_called_once_with("Well-being Tip")
    assert mock_st_full.caption.call_count == 2
    mock_st_full.info.assert_called_once_with("Take a moment to breathe.")


def test_render_wellbeing_tip_panel_http_error_with_response(
    mock_st_full, monkeypatch
) -> None:
    """render_wellbeing_tip_panel handles HTTP error with response."""

    from team_mood_tracker.frontend import dashboard_context
    import requests

    def raise_http_error(*args: Any, **kwargs: Any) -> None:
        error = requests.HTTPError()
        mock_response = MagicMock()
        mock_response.text = "Service unavailable"
        error.response = mock_response
        raise error

    monkeypatch.setattr(
        dashboard_context, "fetch_dashboard_wellbeing_tip", raise_http_error
    )

    dashboard_context.render_wellbeing_tip_panel()

    mock_st_full.warning.assert_called_once()
    warning_message = str(mock_st_full.warning.call_args[0][0])
    assert "unavailable" in warning_message.lower()


def test_render_wellbeing_tip_panel_http_error_without_response(
    mock_st_full, monkeypatch
) -> None:
    """render_wellbeing_tip_panel handles HTTP error without response."""

    from team_mood_tracker.frontend import dashboard_context
    import requests

    def raise_http_error(*args: Any, **kwargs: Any) -> None:
        error = requests.HTTPError("Connection refused")
        error.response = None
        raise error

    monkeypatch.setattr(
        dashboard_context, "fetch_dashboard_wellbeing_tip", raise_http_error
    )

    dashboard_context.render_wellbeing_tip_panel()

    mock_st_full.warning.assert_called_once()


def test_render_wellbeing_tip_panel_request_exception(
    mock_st_full, monkeypatch
) -> None:
    """render_wellbeing_tip_panel handles general request exception."""

    from team_mood_tracker.frontend import dashboard_context
    import requests

    def raise_request_exception(*args: Any, **kwargs: Any) -> None:
        raise requests.RequestException("Network timeout")

    monkeypatch.setattr(
        dashboard_context, "fetch_dashboard_wellbeing_tip", raise_request_exception
    )

    dashboard_context.render_wellbeing_tip_panel()

    mock_st_full.warning.assert_called_once()
    warning_message = str(mock_st_full.warning.call_args[0][0])
    assert "Cannot load" in warning_message
