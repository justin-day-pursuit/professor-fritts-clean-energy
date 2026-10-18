"""
One web request with a short retry, shared by the live tools (v1).

A single network hiccup or a 5xx from a public service should not end a whole agent run.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

# Two retries (three tries in all) ride out a short outage of a public service, such as the electricity-price service
# timing out for a few seconds, which once left a whole live run with a partial plan. The wait grows between tries (1 s,
# then 3 s). Each tool sets its own timeout (10 to 25 seconds), so a call that never answers still gives up in about
# a minute and a half, well inside the run's own 10-minute limit.
RETRIES = 2
WAITS_SECONDS = (1.0, 3.0)


def get_with_retry(url: str, **kwargs: Any) -> httpx.Response:
    """GET a URL; retry on connection errors, timeouts and 5xx replies, then give up and raise."""
    for attempt in range(RETRIES + 1):
        try:
            response = httpx.get(url, **kwargs)
        except (httpx.TransportError, httpx.TimeoutException):
            if attempt == RETRIES:
                raise
        else:
            if response.status_code < 500 or attempt == RETRIES:
                return response
        time.sleep(WAITS_SECONDS[min(attempt, len(WAITS_SECONDS) - 1)])
    raise AssertionError("unreachable")
