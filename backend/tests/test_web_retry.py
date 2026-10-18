"""
The shared web request used by the live tools: how it retries when a public service is slow or down.

Nothing here touches the network. The real request and the clock are replaced with fakes.
"""

from __future__ import annotations

import httpx
import pytest

from tools import web


class FakeResponse:
    """Just enough of a response for the retry code, which only reads the status."""

    def __init__(self, status_code: int):
        self.status_code = status_code


@pytest.fixture
def clock(monkeypatch):
    """Replace sleeping with a list of the waits that were asked for, so tests are instant."""
    waits: list[float] = []
    monkeypatch.setattr(web.time, "sleep", waits.append)
    return waits


def _script(monkeypatch, outcomes):
    """Make each call to httpx.get return or raise the next outcome in the list, and count the calls."""
    calls = {"n": 0}

    def fake_get(url, **kwargs):
        outcome = outcomes[calls["n"]]
        calls["n"] += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(web.httpx, "get", fake_get)
    return calls


def test_a_service_that_times_out_twice_and_then_answers_succeeds(monkeypatch, clock):
    timeout = httpx.ReadTimeout("The read operation timed out")
    calls = _script(monkeypatch, [timeout, timeout, FakeResponse(200)])
    response = web.get_with_retry("https://example.test")
    assert response.status_code == 200
    assert calls["n"] == 3
    # It waited a little, then longer, before each new try.
    assert clock == [1.0, 3.0]


def test_it_gives_up_after_the_last_try_and_raises_the_timeout(monkeypatch, clock):
    timeout = httpx.ReadTimeout("The read operation timed out")
    calls = _script(monkeypatch, [timeout] * 5)
    with pytest.raises(httpx.ReadTimeout):
        web.get_with_retry("https://example.test")
    assert calls["n"] == web.RETRIES + 1


def test_a_server_error_is_retried_and_the_last_one_is_returned(monkeypatch, clock):
    calls = _script(monkeypatch, [FakeResponse(503)] * 5)
    response = web.get_with_retry("https://example.test")
    assert response.status_code == 503
    assert calls["n"] == web.RETRIES + 1


def test_a_missing_page_is_not_retried(monkeypatch, clock):
    calls = _script(monkeypatch, [FakeResponse(404), FakeResponse(200)])
    assert web.get_with_retry("https://example.test").status_code == 404
    assert calls["n"] == 1
    assert clock == []


def test_the_worst_case_wait_stays_short(monkeypatch):
    # Each try waits at most 25 seconds for an answer (the slowest tool), plus the pauses between tries.
    from tools import live_rates

    worst = (web.RETRIES + 1) * live_rates.TIMEOUT_SECONDS + sum(web.WAITS_SECONDS)
    assert worst <= 120
