"""
Mock tool fixtures and calculate tool tests.
"""

from __future__ import annotations

import json
import os

import pytest
from django.conf import settings

from mocks.mock_mode import FIXTURES_ROOT, load_fixture
from tools.calculate import CalculateInput, run_calculate
from tools.registry import execute_tool, list_tool_names


CASE = "case1_queens_library"


@pytest.mark.parametrize("tool_name", list_tool_names())
def test_mock_fixtures_have_provenance(tool_name):
    if tool_name in ("get_building_profile", "calculate"):
        pytest.skip("live/session tools have no fixture file")
    result = load_fixture(CASE, tool_name)
    assert result.source_url
    assert result.retrieved_at
    assert result.dataset_version
    assert result.mock is True


def test_calculate_c1_c4():
    c1 = run_calculate(CalculateInput(formula="C1", inputs={"roof_area_sqft": 6000, "setback_factor": 0.55}))
    assert c1.data["value"] == pytest.approx(3300.0)
    c2 = run_calculate(CalculateInput(formula="C2", inputs={"usable_roof_sqft": 3300, "sqft_per_kw": 66}))
    assert c2.data["value"] == pytest.approx(50.0, rel=0.01)
    c3 = run_calculate(CalculateInput(formula="C3", inputs={"annual_solar_kwh": 60000, "annual_use_kwh": 310000}))
    assert c3.data["value"] == pytest.approx(60000 / 310000, rel=0.01)
    c4 = run_calculate(CalculateInput(formula="C4", inputs={"annual_solar_kwh": 60000, "avg_rate_usd_per_kwh": 0.22}))
    assert c4.data["value"] == pytest.approx(13200.0, rel=0.01)


def _queens_profile() -> dict:
    return json.loads((FIXTURES_ROOT / CASE / "intake.json").read_text(encoding="utf-8"))


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


def _fake_httpx_get(url, params=None, timeout=None):
    if "geosearch" in url:
        return _FakeResponse(
            {
                "features": [
                    {
                        "geometry": {"coordinates": [-73.828843, 40.757744]},
                        "properties": {
                            "label": "41-17 MAIN STREET, Flushing, NY, USA",
                            "borough": "Queens",
                            "postalcode": "11355",
                            "match_type": "fallback",
                            "confidence": 0.8,
                        },
                    }
                ]
            }
        )
    return _FakeResponse(
        {
            "errors": [],
            "version": "8.5.0",
            "outputs": {
                "ac_annual": 61893.6,
                "capacity_factor": 14.13,
                "solrad_annual": 4.41,
                "ac_monthly": [1.0] * 12,
            },
            "station_info": {"weather_data_source": "NSRDB test"},
        }
    )


def test_live_mode_keeps_fixtures_for_tools_without_a_live_version(monkeypatch):
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    result = execute_tool("get_utility_rates", {}, session_profile={}, fixture_case=CASE)
    assert result.mock is True


def test_live_solar_returns_real_shaped_result(monkeypatch):
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("tools.live_solar.httpx.get", _fake_httpx_get)

    result = execute_tool("get_solar_production", {}, session_profile=_queens_profile(), fixture_case=CASE)

    assert result.mock is False
    assert result.data["system_kw_dc"] == pytest.approx(50.0)  # 6000 sq ft roof, C1 then C2
    assert result.data["annual_ac_kwh"] == pytest.approx(61893.6)
    assert result.data["capacity_factor"] == pytest.approx(0.1413)
    assert result.data["pvwatts_inputs"]["lat"] == pytest.approx(40.757744)
    assert result.source_url.startswith("https://developer.nlr.gov/")
    assert result.dataset_version == "pvwatts-v8.5.0"
    assert result.retrieved_at.endswith("Z")
    assert "address_match_approximate" in result.flags
    assert "test-key" not in result.model_dump_json()


def test_live_solar_accepts_an_explicit_system_size(monkeypatch):
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("tools.live_solar.httpx.get", _fake_httpx_get)

    result = execute_tool("get_solar_production", {"system_kw": 30}, session_profile=_queens_profile(), fixture_case=CASE)

    assert result.data["system_kw_dc"] == 30


def test_live_solar_needs_an_api_key(monkeypatch):
    from tools.live_solar import LiveSolarError

    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.delenv("NLR_API_KEY", raising=False)
    with pytest.raises(LiveSolarError, match="NLR_API_KEY"):
        execute_tool("get_solar_production", {}, session_profile=_queens_profile(), fixture_case=CASE)


@pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the real APIs")
def test_live_solar_against_real_apis(monkeypatch):
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    result = execute_tool("get_solar_production", {}, session_profile=_queens_profile(), fixture_case=CASE)
    assert 50000 < result.data["annual_ac_kwh"] < 75000
