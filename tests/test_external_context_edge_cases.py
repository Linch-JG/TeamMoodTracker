"""Additional tests for external context error handling."""

from __future__ import annotations

import pytest

from team_mood_tracker.backend.external_context import (
    ExternalContextError,
    fetch_dashboard_wellbeing_tip,
    validate_external_api_url,
)


def test_validate_external_api_url_accepts_https() -> None:
    """validate_external_api_url accepts valid HTTPS URLs."""

    result = validate_external_api_url("https://example.com/api")

    assert result == "https://example.com/api"


def test_validate_external_api_url_rejects_http() -> None:
    """validate_external_api_url rejects HTTP URLs."""

    with pytest.raises(ExternalContextError) as exc_info:
        validate_external_api_url("http://example.com/api")

    assert "HTTPS" in str(exc_info.value)


def test_validate_external_api_url_rejects_no_netloc() -> None:
    """validate_external_api_url rejects URLs without netloc."""

    with pytest.raises(ExternalContextError) as exc_info:
        validate_external_api_url("https:///path")

    assert "HTTPS" in str(exc_info.value)


def test_fetch_dashboard_wellbeing_tip_rejects_non_list(monkeypatch) -> None:
    """fetch_dashboard_wellbeing_tip raises error when response is not a list."""

    def fake_perform_advice_request(base_url: str | None = None) -> object:
        return {"not": "a list"}

    monkeypatch.setattr(
        "team_mood_tracker.backend.external_context._perform_advice_request",
        fake_perform_advice_request,
    )

    with pytest.raises(ExternalContextError) as exc_info:
        fetch_dashboard_wellbeing_tip()

    assert "not return a quote" in str(exc_info.value)


def test_fetch_dashboard_wellbeing_tip_rejects_empty_list(monkeypatch) -> None:
    """fetch_dashboard_wellbeing_tip raises error when response is an empty list."""

    def fake_perform_advice_request(base_url: str | None = None) -> object:
        return []

    monkeypatch.setattr(
        "team_mood_tracker.backend.external_context._perform_advice_request",
        fake_perform_advice_request,
    )

    with pytest.raises(ExternalContextError) as exc_info:
        fetch_dashboard_wellbeing_tip()

    assert "not return a quote" in str(exc_info.value)


def test_fetch_dashboard_wellbeing_tip_rejects_non_dict_item(monkeypatch) -> None:
    """fetch_dashboard_wellbeing_tip raises error when first item is not a dict."""

    def fake_perform_advice_request(base_url: str | None = None) -> object:
        return ["not a dict"]

    monkeypatch.setattr(
        "team_mood_tracker.backend.external_context._perform_advice_request",
        fake_perform_advice_request,
    )

    with pytest.raises(ExternalContextError) as exc_info:
        fetch_dashboard_wellbeing_tip()

    assert "not return a quote" in str(exc_info.value)


def test_fetch_dashboard_wellbeing_tip_rejects_missing_keys(monkeypatch) -> None:
    """fetch_dashboard_wellbeing_tip raises error when required keys are missing."""

    def fake_perform_advice_request(base_url: str | None = None) -> object:
        return [{"invalid": "keys"}]

    monkeypatch.setattr(
        "team_mood_tracker.backend.external_context._perform_advice_request",
        fake_perform_advice_request,
    )

    with pytest.raises(ExternalContextError) as exc_info:
        fetch_dashboard_wellbeing_tip()

    assert "schema" in str(exc_info.value)


def test_fetch_dashboard_wellbeing_tip_rejects_empty_advice(monkeypatch) -> None:
    """fetch_dashboard_wellbeing_tip raises error when advice is empty."""

    def fake_perform_advice_request(base_url: str | None = None) -> object:
        return [{"q": "  ", "a": "Someone"}]

    monkeypatch.setattr(
        "team_mood_tracker.backend.external_context._perform_advice_request",
        fake_perform_advice_request,
    )

    with pytest.raises(ExternalContextError) as exc_info:
        fetch_dashboard_wellbeing_tip()

    assert "empty" in str(exc_info.value)


def test_fetch_dashboard_wellbeing_tip_rejects_empty_author(monkeypatch) -> None:
    """fetch_dashboard_wellbeing_tip raises error when author is empty."""

    def fake_perform_advice_request(base_url: str | None = None) -> object:
        return [{"q": "Some advice", "a": "   "}]

    monkeypatch.setattr(
        "team_mood_tracker.backend.external_context._perform_advice_request",
        fake_perform_advice_request,
    )

    with pytest.raises(ExternalContextError) as exc_info:
        fetch_dashboard_wellbeing_tip()

    assert "empty" in str(exc_info.value)
