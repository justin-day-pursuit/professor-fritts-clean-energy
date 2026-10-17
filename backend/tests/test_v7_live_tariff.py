"""Tests for the live tariff candidates from OpenEI (the answer is faked; no network, no key needed)."""

import pytest

from mocks.mock_mode import forced_tool_mode
from agent.notes import AgentNotes
from tools import live_tariff
from tools.base import ToolUnavailableError
from tools.live_tariff import fetch_live_tariff, pick_candidates
from tools.ny_rules_rates import get_utility_tariff


def _item(name, label="abc", start=1738393200, end=None, fixed=33):
    return {"name": name, "label": label, "startdate": start, "enddate": end, "fixedchargefirstmeter": fixed, "fixedchargeunits": "$/month"}


class _Reply:
    status_code = 200

    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


def test_only_current_nyc_general_service_tariffs_are_candidates():
    items = [
        _item("SC-2 - General Small [NYC]", "a"),
        _item("SC-2 - General Small - Zone I [NYC]", "b"),
        _item("SC-2 - General Small [Westchester]", "c"),
        _item("SC-9 - General Large Low Tension Service [NYC]", "d"),
        _item("SC-9 - General Large High Tension Service [NYC]", "e", end=1700000000),
        _item("SC-8 - Multiple Dwellings Redistribution [NYC]", "f"),
    ]
    names = [c["tariff_name"] for c in pick_candidates(items)]
    assert names == ["SC-2 - General Small [NYC]", "SC-9 - General Large Low Tension Service [NYC]"]


def test_candidates_carry_a_link_and_no_price(monkeypatch):
    monkeypatch.setenv("OPENEI_API_KEY", "k")
    monkeypatch.setattr(live_tariff, "get_with_retry", lambda *a, **k: _Reply({"items": [_item("SC-9 - General Large Low Tension Service [NYC]", "d")]}))
    result = fetch_live_tariff({"utility": "Con Edison"})
    assert result.mock is False and "tariff_needs_user_confirmation" in result.flags
    candidate = result.data["candidate_tariffs"][0]
    assert candidate["openei_url"].endswith("/d") and candidate["fixed_charge_usd_per_month"] == 33
    assert "energy_charge_usd_per_kwh" not in result.data and "no energy price" in result.data["note"]


def test_no_key_or_no_tariffs_is_unavailable_not_sample(monkeypatch):
    monkeypatch.delenv("OPENEI_API_KEY", raising=False)
    with pytest.raises(ToolUnavailableError):
        fetch_live_tariff({})
    monkeypatch.setenv("OPENEI_API_KEY", "k")
    monkeypatch.setattr(live_tariff, "get_with_retry", lambda *a, **k: _Reply({"items": []}))
    with pytest.raises(ToolUnavailableError):
        fetch_live_tariff({"utility": "Con Edison"})


def test_tariff_pages_become_source_links(monkeypatch):
    monkeypatch.setenv("OPENEI_API_KEY", "k")
    monkeypatch.setattr(live_tariff, "get_with_retry", lambda *a, **k: _Reply({"items": [_item("SC-2 - General Small [NYC]", "a")]}))
    notes = AgentNotes()
    notes.record_tool_result("get_utility_tariff", fetch_live_tariff({}))
    assert any(s["url"].endswith("/a") for s in notes.source_links)


def test_mock_mode_still_returns_the_saved_tariff():
    with forced_tool_mode("mock"):
        assert get_utility_tariff("case1_queens_library", {}).mock is True
