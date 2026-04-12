"""External reflection quote integration for the dashboard."""

from __future__ import annotations

import json
import os
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from team_mood_tracker.backend.api_schemas import WellbeingTip

WELLBEING_ADVICE_API_URL_ENV = "TEAM_MOOD_WELLBEING_API_URL"
DEFAULT_WELLBEING_ADVICE_API_URL = "https://zenquotes.io/api/random"
EXTERNAL_REQUEST_TIMEOUT_SECONDS = 5


class ExternalContextError(RuntimeError):
    """Raised when the external reflection provider cannot be used safely."""


def validate_external_api_url(api_url: str) -> str:
    """Allow only HTTPS URLs for the external reflection provider."""

    parsed_url = urlparse(api_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ExternalContextError("Reflection provider URL must use HTTPS.")

    return api_url


def _quote_fields_from_mapping(quote: dict) -> tuple[str, str]:
    """Extract advice and author strings from a ZenQuotes-style mapping."""

    try:
        advice = str(quote["q"]).strip()
        author = str(quote["a"]).strip()
    except (KeyError, TypeError, ValueError) as error:
        raise ExternalContextError(
            "Reflection provider response schema was not recognized."
        ) from error
    return advice, author


def _first_quote_mapping(payload: object) -> dict:
    """Return the first quote object from a ZenQuotes-style JSON list."""

    if not (isinstance(payload, list) and len(payload) > 0):
        raise ExternalContextError("Reflection provider did not return a quote.")

    first = payload[0]
    if not isinstance(first, dict):
        raise ExternalContextError("Reflection provider did not return a quote.")
    return first


def _non_empty_tip(advice: str, author: str) -> WellbeingTip:
    """Build a tip or raise when text fields are blank."""

    if not advice or not author:
        raise ExternalContextError("Reflection provider returned an empty quote.")
    return WellbeingTip(
        tip_id=1,
        advice=advice,
        author=author,
        source="ZenQuotes",
    )


def _wellbeing_tip_from_payload(payload: object) -> WellbeingTip:
    """Validate JSON payload shape and build a WellbeingTip."""

    quote = _first_quote_mapping(payload)
    advice, author = _quote_fields_from_mapping(quote)
    return _non_empty_tip(advice, author)


def fetch_dashboard_wellbeing_tip(base_url: str | None = None) -> WellbeingTip:
    """Fetch a short reflection quote for the dashboard."""

    payload = _perform_advice_request(base_url)
    return _wellbeing_tip_from_payload(payload)


def _perform_advice_request(base_url: str | None = None) -> object:
    """Perform the outbound request to the reflection provider."""

    resolved_base_url = base_url
    if resolved_base_url is None:
        resolved_base_url = os.getenv(
            WELLBEING_ADVICE_API_URL_ENV,
            DEFAULT_WELLBEING_ADVICE_API_URL,
        )
    advice_api_url = validate_external_api_url(resolved_base_url)
    try:
        external_request = request.Request(
            advice_api_url,
            headers={"Accept": "application/json"},
        )
        with request.urlopen(  # nosec B310
            external_request,
            timeout=EXTERNAL_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            return json.load(response)
    except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as error:
        raise ExternalContextError("Reflection provider request failed.") from error
