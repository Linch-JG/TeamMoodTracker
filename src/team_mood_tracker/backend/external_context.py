"""External reflection quote integration for the dashboard."""

from __future__ import annotations

import json
import os
from urllib import request
from urllib.error import HTTPError, URLError

from team_mood_tracker.backend.api_schemas import WellbeingTip


WELLBEING_ADVICE_API_URL_ENV = "TEAM_MOOD_WELLBEING_API_URL"
DEFAULT_WELLBEING_ADVICE_API_URL = "https://zenquotes.io/api/random"
EXTERNAL_REQUEST_TIMEOUT_SECONDS = 5


class ExternalContextError(RuntimeError):
    """Raised when the external reflection provider cannot be used safely."""


def fetch_dashboard_wellbeing_tip(base_url: str | None = None) -> WellbeingTip:
    """Fetch a short reflection quote for the dashboard."""

    payload = _perform_advice_request(base_url)
    if not isinstance(payload, list) or not payload:
        raise ExternalContextError("Reflection provider did not return a quote.")

    quote = payload[0]
    if not isinstance(quote, dict):
        raise ExternalContextError("Reflection provider did not return a quote.")

    try:
        advice = str(quote["q"]).strip()
        author = str(quote["a"]).strip()
    except (KeyError, TypeError, ValueError) as error:
        raise ExternalContextError("Reflection provider response schema was not recognized.") from error

    if not advice or not author:
        raise ExternalContextError("Reflection provider returned an empty quote.")

    return WellbeingTip(
        tip_id=1,
        advice=advice,
        author=author,
        source="ZenQuotes",
    )


def _perform_advice_request(base_url: str | None = None) -> object:
    """Perform the outbound request to the reflection provider."""

    advice_api_url = base_url or os.getenv(
        WELLBEING_ADVICE_API_URL_ENV,
        DEFAULT_WELLBEING_ADVICE_API_URL,
    )
    try:
        external_request = request.Request(
            advice_api_url,
            headers={"Accept": "application/json"},
        )
        with request.urlopen(external_request, timeout=EXTERNAL_REQUEST_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as error:
        raise ExternalContextError("Reflection provider request failed.") from error
