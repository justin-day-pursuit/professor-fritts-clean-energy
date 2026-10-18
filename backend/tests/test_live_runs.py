"""
Starting a run in the background and checking on it, as the design page does.

These use the scripted model (a saved transcript) and mock tools, so no test calls Claude or a live service.
"""

from __future__ import annotations

import time

import pytest

CASE = "case1_queens_library"


@pytest.fixture(autouse=True)
def scripted_env(monkeypatch):
    """Scripted model and mock tools for every test here, so nothing can reach Claude."""
    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("TOOL_MODE", "mock")
    from django.conf import settings

    monkeypatch.setattr(settings, "LLM_PROVIDER", "scripted", raising=False)
    monkeypatch.setattr(settings, "TOOL_MODE", "mock", raising=False)


def _session(api_client) -> str:
    """A new session with the Queens library's details and its fixture, so the scripted model has a transcript to play."""
    from mocks.catalog import load_case

    profile, _question = load_case(CASE)
    response = api_client.post("/api/sessions", json={"profile": profile, "fixture_case": CASE})
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def _wait_until_finished(api_client, session_id: str, seconds: float = 60) -> dict:
    """Ask for the latest run every moment, as the page does, until it is no longer running."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        response = api_client.get(f"/api/sessions/{session_id}/latest-run")
        if response.status_code == 200 and response.json()["status"] not in ("queued", "running"):
            return response.json()
        time.sleep(0.2)
    raise AssertionError("the run did not finish in time")


def test_a_run_starts_at_once_and_finishes_with_a_plan(api_client):
    session_id = _session(api_client)
    started = api_client.post(f"/api/sessions/{session_id}/runs", json={"content": "How can we cut grid power 30% by 2030?"})
    assert started.status_code == 202
    assert started.json() == {"session_id": session_id, "started": True}

    run = _wait_until_finished(api_client, session_id)
    assert run["status"] in ("done", "partial")
    assert run["output"]["plan_summary"]
    kinds = [event["kind"] for event in run["events"]]
    assert "tool_call" in kinds and "final" in kinds


def test_latest_run_is_404_before_any_run(api_client):
    session_id = _session(api_client)
    assert api_client.get(f"/api/sessions/{session_id}/latest-run").status_code == 404


def test_an_unknown_session_is_404(api_client):
    response = api_client.post("/api/sessions/00000000-0000-0000-0000-000000000000/runs", json={"content": "hi"})
    assert response.status_code == 404


def test_a_second_start_while_one_is_going_is_refused(api_client):
    from uuid import UUID

    from api.routers import live_runs

    session_id = _session(api_client)
    # Pretend a run is already going for this session.
    with live_runs._active_lock:
        live_runs._active.add(UUID(session_id))
    try:
        response = api_client.post(f"/api/sessions/{session_id}/runs", json={"content": "again"})
        assert response.status_code == 409
    finally:
        with live_runs._active_lock:
            live_runs._active.discard(UUID(session_id))


def test_the_daily_cap_stops_paid_runs_with_a_plain_message(api_client, monkeypatch):
    from django.conf import settings

    from api.routers import live_runs

    monkeypatch.setattr(settings, "LLM_PROVIDER", "anthropic", raising=False)
    monkeypatch.setattr(live_runs, "paid_runs_today", lambda: 25)
    session_id = _session(api_client)
    response = api_client.post(f"/api/sessions/{session_id}/runs", json={"content": "go"})
    assert response.status_code == 429
    assert "tomorrow" in response.json()["detail"]
    # Nothing was started, so nothing is left marked as running.
    assert live_runs._active == set()


def test_runs_on_the_scripted_model_are_never_capped(api_client, monkeypatch):
    from api.routers import live_runs

    monkeypatch.setattr(live_runs, "paid_runs_today", lambda: 10_000)
    session_id = _session(api_client)
    assert api_client.post(f"/api/sessions/{session_id}/runs", json={"content": "go"}).status_code == 202
    _wait_until_finished(api_client, session_id)


@pytest.mark.parametrize("value,expected", [("40", 40), ("0", 25), ("-3", 25), ("lots", 25)])
def test_the_daily_cap_setting_falls_back_to_the_default_when_it_is_not_a_positive_number(monkeypatch, value, expected):
    from api.routers import live_runs

    monkeypatch.setenv("LIVE_RUNS_PER_DAY", value)
    assert live_runs.runs_per_day() == expected
