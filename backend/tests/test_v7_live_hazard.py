"""Tests for the live FEMA flood-zone lookup (no network: the map service and geocoder are faked)."""

import pytest

from mocks.mock_mode import forced_tool_mode
from tools import live_hazard
from tools.base import ToolUnavailableError
from tools.climate_risk import get_hazard_context
from tools.live_hazard import fetch_live_hazard, parse_flood_features

PLACE = {"label": "480 Van Brunt St, Brooklyn", "lat": 40.676, "lon": -74.016, "confidence": 1.0, "bbl": "3005820001"}


class _Reply:
    """A stand-in for an HTTP reply from the FEMA map service."""

    def __init__(self, body, status=200):
        self._body, self.status_code = body, status

    def json(self):
        return self._body


def _feature(zone, subtype=""):
    return {"attributes": {"FLD_ZONE": zone, "ZONE_SUBTY": subtype, "SFHA_TF": "F"}}


def test_shaded_x_is_not_high_risk():
    out = parse_flood_features([_feature("X", "0.2 PCT ANNUAL CHANCE FLOOD HAZARD")])
    assert out["flood_zone"] == "X" and out["special_flood_hazard_area"] is False


def test_high_risk_zone_beats_x_when_a_point_has_two():
    out = parse_flood_features([_feature("X"), _feature("AE")])
    assert out["flood_zone"] == "AE" and out["special_flood_hazard_area"] is True


def test_no_polygon_is_reported_as_unmapped_not_zone_x():
    assert parse_flood_features([])["flood_zone"] is None


def test_live_result_names_its_limits_and_is_not_mock(monkeypatch):
    monkeypatch.setattr(live_hazard, "geocode_nyc_address", lambda a, b: PLACE)
    monkeypatch.setattr(live_hazard, "get_with_retry", lambda *a, **k: _Reply({"features": [_feature("AE")]}))
    result = fetch_live_hazard({"address": "480 Van Brunt St", "borough": "Brooklyn"})
    assert result.mock is False
    assert result.data["flood_zone"] == "AE"
    assert "preliminary map was not checked" in result.data["notes"]
    assert "hazard_partial" in result.flags


def test_failures_are_unavailable_not_invented(monkeypatch):
    with pytest.raises(ToolUnavailableError):
        fetch_live_hazard({})
    monkeypatch.setattr(live_hazard, "geocode_nyc_address", lambda a, b: PLACE)
    monkeypatch.setattr(live_hazard, "get_with_retry", lambda *a, **k: _Reply({"error": "x"}))
    with pytest.raises(ToolUnavailableError):
        fetch_live_hazard({"address": "480 Van Brunt St"})


def test_mock_mode_still_returns_the_saved_fixture():
    with forced_tool_mode("mock"):
        result = get_hazard_context("case1_queens_library", {"address": "anything"})
    assert result.mock is True
