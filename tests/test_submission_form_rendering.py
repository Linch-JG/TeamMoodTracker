"""Comprehensive tests for submission form rendering with mocks."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def mock_st_and_requests(monkeypatch) -> tuple[MagicMock, MagicMock]:
    """Mock Streamlit and requests for submission form testing."""

    mock_st = MagicMock()
    mock_st.form.return_value.__enter__ = MagicMock()
    mock_st.form.return_value.__exit__ = MagicMock(return_value=False)

    mock_requests = MagicMock()

    import streamlit
    import requests

    for attr in [
        "title",
        "write",
        "form",
        "text_input",
        "selectbox",
        "slider",
        "text_area",
        "form_submit_button",
        "error",
        "success",
    ]:
        monkeypatch.setattr(streamlit, attr, getattr(mock_st, attr))

    monkeypatch.setattr(requests, "post", mock_requests.post)
    monkeypatch.setattr(requests, "HTTPError", requests.HTTPError)
    monkeypatch.setattr(requests, "RequestException", requests.RequestException)

    return mock_st, mock_requests


def test_render_submission_form_not_submitted(mock_st_and_requests) -> None:
    """render_submission_form handles case when form not submitted."""

    mock_st, mock_requests = mock_st_and_requests
    mock_st.form_submit_button.return_value = False

    from team_mood_tracker.frontend import submission_form

    submission_form.render_submission_form(show_heading=False)

    mock_st.form.assert_called_once()
    mock_st.text_input.assert_called_once()
    mock_st.selectbox.assert_called_once()
    mock_st.slider.assert_called_once()
    mock_st.text_area.assert_called_once()


def test_render_submission_form_with_heading(mock_st_and_requests) -> None:
    """render_submission_form shows heading when requested."""

    mock_st, mock_requests = mock_st_and_requests
    mock_st.form_submit_button.return_value = False

    from team_mood_tracker.frontend import submission_form

    submission_form.render_submission_form(show_heading=True)

    mock_st.title.assert_called_once()
    mock_st.write.assert_called_once()


def test_render_submission_form_empty_user(mock_st_and_requests) -> None:
    """render_submission_form shows error when user name is empty."""

    mock_st, mock_requests = mock_st_and_requests
    mock_st.form_submit_button.return_value = True
    mock_st.text_input.return_value = "  "

    from team_mood_tracker.frontend import submission_form

    submission_form.render_submission_form(show_heading=False)

    mock_st.error.assert_called_once()


def test_render_submission_form_http_error(mock_st_and_requests, monkeypatch) -> None:
    """render_submission_form handles HTTP errors from API."""

    mock_st, mock_requests = mock_st_and_requests
    mock_st.form_submit_button.return_value = True
    mock_st.text_input.return_value = "Alice"
    mock_st.selectbox.return_value = "happy"
    mock_st.slider.return_value = 5
    mock_st.text_area.return_value = "Great day"

    import requests

    def raise_http_error(*args: Any, **kwargs: Any) -> None:
        error = requests.HTTPError()
        error.response = MagicMock()
        error.response.text = "API error"
        raise error

    from team_mood_tracker.frontend import submission_form

    monkeypatch.setattr(submission_form, "submit_mood_entry", raise_http_error)

    submission_form.render_submission_form(show_heading=False)

    assert mock_st.error.called


def test_render_submission_form_request_exception(
    mock_st_and_requests, monkeypatch
) -> None:
    """render_submission_form handles connection errors."""

    mock_st, mock_requests = mock_st_and_requests
    mock_st.form_submit_button.return_value = True
    mock_st.text_input.return_value = "Alice"
    mock_st.selectbox.return_value = "happy"
    mock_st.slider.return_value = 5
    mock_st.text_area.return_value = ""

    import requests

    def raise_request_error(*args: Any, **kwargs: Any) -> None:
        raise requests.RequestException("Connection failed")

    from team_mood_tracker.frontend import submission_form

    monkeypatch.setattr(submission_form, "submit_mood_entry", raise_request_error)

    submission_form.render_submission_form(show_heading=False)

    assert mock_st.error.called


def test_render_submission_form_success(mock_st_and_requests, monkeypatch) -> None:
    """render_submission_form shows success message when entry saved."""

    mock_st, mock_requests = mock_st_and_requests
    mock_st.form_submit_button.return_value = True
    mock_st.text_input.return_value = "Alice"
    mock_st.selectbox.return_value = "happy"
    mock_st.slider.return_value = 5
    mock_st.text_area.return_value = "Great day"

    def return_entry(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"id": 1, "user": "Alice", "mood": "happy", "rating": 5}

    from team_mood_tracker.frontend import submission_form

    monkeypatch.setattr(submission_form, "submit_mood_entry", return_entry)

    submission_form.render_submission_form(show_heading=False)

    mock_st.success.assert_called_once()
