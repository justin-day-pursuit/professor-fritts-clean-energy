"""
Tests for the replay endpoint behind the planner's "replay a saved demo" menu (v6).

A replay plays a saved run back through our real harness, so the user sees the plan, the run log and the checks
without spending Claude credits. The tests that matter most simulate a server set to live Claude and live tools,
and check that a replay still touches neither.
"""

from __future__ import annotations

import anthropic
import httpx
import pytest
from django.conf import settings

from api.routers.replay import REPLAY_CASES
from mocks.mock_mode import get_tool_mode


def test_the_menu_lists_every_saved_demo_with_whether_it_is_a_recording(api_client):
    """The list has the six saved demos, each marked as a recording."""
    cases = api_client.get("/api/replay/cases").json()["cases"]
    assert [c["id"] for c in cases] == [c["id"] for c in REPLAY_CASES]
    kinds = {c["id"]: c["kind"] for c in cases}
    assert all(kind == "recorded" for kind in kinds.values())
    assert all(c["question"] and c["label"] and c["tag"] for c in cases)


@pytest.mark.parametrize(("case_id", "status"), [
    ("plan_ps236_bronx", "done"),
    ("plan_ps38_staten_island", "done"),
    ("plan_red_hook_rec_center", "done"),
    ("plan_jefferson_market_library", "partial"),
    ("plan_ps24_bronx_existing_solar", "done"),
    ("plan_flushing_library_queens", "done"),
])
def test_each_saved_demo_replays_to_its_recorded_outcome(api_client, case_id, status):
    """Each replay returns the session, the assistant plan message, and a run with its full event log."""
    body = api_client.post(f"/api/replay/{case_id}").json()
    assert body["run"]["status"] == status
    assert body["session"]["fixture_case"] == case_id and body["session"]["profile"]["building_name"]
    assert body["message"]["role"] == "assistant"
    kinds = {e["kind"] for e in body["run"]["events"]}
    assert {"check1", "tool_call", "tool_result", "check4", "final"} <= kinds
    assert len(body["run"]["events"]) > 20 and body["run"]["output"]["roadmap"]["sections"]
    assert body["case"]["id"] == case_id


def test_a_replay_never_calls_claude_or_a_live_service_even_on_a_live_server(api_client, monkeypatch):
    """With the server set to live Claude and live tools, a replay still uses neither: they raise if touched."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(settings, "TOOL_MODE", "live")

    def forbidden(*args, **kwargs):
        raise AssertionError("A replay must not reach Claude or the network.")

    monkeypatch.setattr(anthropic, "Anthropic", forbidden)
    monkeypatch.setattr(httpx, "get", forbidden)
    body = api_client.post("/api/replay/plan_ps38_staten_island").json()
    assert body["run"]["status"] == "done"
    assert body["run"]["llm_provider"] == "scripted" and body["run"]["tool_mode"] == "mock"
    assert not [e for e in body["run"]["events"] if e["kind"] == "usage"]  # no model call, so no spend entries


def test_the_forced_mock_mode_does_not_leak_to_other_requests(api_client, monkeypatch):
    """After a replay the server's own tool mode is exactly what it was, so live runs are unaffected."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    assert get_tool_mode() == "live"
    api_client.post("/api/replay/plan_red_hook_rec_center")
    assert get_tool_mode() == "live"


@pytest.mark.parametrize("case_id", ["case1_queens_library", "case3_park_rec_center", "no_such_case", "real9_missing"])
def test_only_the_listed_demos_can_be_replayed(api_client, case_id):
    """Any case that is not in the menu returns 404, including real fixture folders that exist."""
    response = api_client.post(f"/api/replay/{case_id}")
    assert response.status_code == 404 and "No saved demo" in response.json()["detail"]
