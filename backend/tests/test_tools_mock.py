"""
Mock tool fixtures and calculate tool tests.
"""

from __future__ import annotations

import os

import pytest

from mocks.mock_mode import LiveModeNotAvailableError, load_fixture
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


def test_live_mode_raises(monkeypatch):
    monkeypatch.setenv("TOOL_MODE", "live")
    from django.conf import settings

    settings.TOOL_MODE = "live"
    with pytest.raises(LiveModeNotAvailableError):
        execute_tool("get_solar_production", {}, session_profile={}, fixture_case=CASE)
