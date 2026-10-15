"""
One web request with a short retry, shared by the live tools (v1).

A single network hiccup or a 5xx from a public service should not end a whole agent run.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

# One retry keeps the worst case for a hanging service to two timeouts plus a short wait; each tool sets
# its own timeout (10 to 20 seconds), so a single call gives up well inside a minute.
RETRIES = 1
WAIT_SECONDS = 1.0


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
        time.sleep(WAIT_SECONDS)
    raise AssertionError("unreachable")
