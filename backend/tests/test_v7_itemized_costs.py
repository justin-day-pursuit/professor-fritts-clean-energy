"""Tests for real solar prices (NYSERDA project costs) and the itemized bill in the scenario model (no network)."""

from agent.scenarios import FinancialModelInput, run_financial_model
from mocks.mock_mode import forced_tool_mode
from tools import solar_costs
from tools.registry import _with_real_solar_price
from tools.solar_costs import band_for, cost_percentiles


def _rows(n, kw=200.0, per_kw=3000.0):
    """n projects of the same size, with costs spread evenly from per_kw to 2 x per_kw."""
    return [{"project_cost": str(kw * per_kw * (1 + i / n)), "totalnameplatekwdc": str(kw)} for i in range(n)]


def _inp(**over):
    base = dict(
        scenario_id="B", floor_area_sqft=40000, annual_use_kwh=450000, budget_usd=800000, full_array_kw_dc=85.5,
        annual_solar_kwh_low=90000, annual_solar_kwh_high=110000, price_low_usd_per_kwh=0.2, price_high_usd_per_kwh=0.3,
    )
    base.update(over)
    return FinancialModelInput(**base)


def test_bands_follow_array_size():
    assert band_for(10) == (25.0, 100.0)
    assert band_for(85) == (25.0, 100.0)
    assert band_for(300) == (100.0, 500.0)
    assert band_for(900) == (500.0, 5000.0)


def test_percentiles_ordered_and_counted():
    out = cost_percentiles(_rows(40), (100.0, 500.0))
    assert out["p25_usd_per_kw"] < out["p50_usd_per_kw"] < out["p75_usd_per_kw"]
    assert out["projects"] == 40


def test_too_few_projects_gives_no_range():
    assert cost_percentiles(_rows(5), (100.0, 500.0)) is None


def test_bad_rows_are_skipped():
    rows = _rows(30) + [{"project_cost": "0", "totalnameplatekwdc": "200"}, {"project_cost": "x"}, {}]
    assert cost_percentiles(rows, (100.0, 500.0))["projects"] == 30


def test_itemized_bill_adds_up_to_upfront_cost():
    data = run_financial_model(_inp()).data
    assert [i["item"] for i in data["cost_items"]][:2] == ["Standard efficiency package", "Rooftop solar"]
    low = sum(i["usd"][0] for i in data["cost_items"] if i["usd"][0] > 0)
    assert abs(low - data["upfront_usd"][0]) <= len(data["cost_items"])
    assert "placeholder" in data["cost_items"][0]["basis"]


def test_real_price_replaces_placeholder_and_is_quoted():
    priced = _inp(solar_usd_per_kw_low=2500.0, solar_usd_per_kw_high=3500.0, solar_price_basis="NYSERDA test")
    data = run_financial_model(priced).data
    solar = [i for i in data["cost_items"] if i["item"] == "Rooftop solar"][0]
    assert "$2,500-3,500/kW" in solar["basis"] and "NYSERDA test" in solar["basis"]
    assert "NYSERDA test" in data["assumption_text"]
    assert "placeholder" in data["assumption_text"]  # battery and efficiency are still placeholders, and say so


def test_live_mode_fills_price_and_mock_mode_does_not(monkeypatch):
    found = {"p25_usd_per_kw": 2800, "p75_usd_per_kw": 4200, "projects": 558, "band_kw": [25.0, 100.0],
             "since": "2022-01-01", "source_url": "https://data.ny.gov/x"}
    monkeypatch.setattr(solar_costs, "fetch_solar_cost_range", lambda kw: found)
    with forced_tool_mode("live"):
        updated, flags = _with_real_solar_price(_inp())
    assert updated.solar_usd_per_kw_low == 2800 and updated.solar_usd_per_kw_high == 4200 and flags == []
    assert "558 completed NYC" in updated.solar_price_basis
    with forced_tool_mode("mock"):
        same, flags = _with_real_solar_price(_inp())
    assert same.solar_usd_per_kw_low is None and flags == []


def test_failed_lookup_keeps_placeholder_and_flags_it(monkeypatch):
    def boom(kw):
        raise solar_costs.SolarCostError("down")

    monkeypatch.setattr(solar_costs, "fetch_solar_cost_range", boom)
    with forced_tool_mode("live"):
        same, flags = _with_real_solar_price(_inp())
    assert same.solar_usd_per_kw_low is None and flags == ["solar_price_placeholder"]


# ---- battery price from NYSERDA's NYC storage projects ----

from tools.solar_costs import storage_percentiles


def _storage_rows(n, kwh=200.0, per_kwh=500.0):
    """n storage projects whose cost per kWh runs from per_kwh up to twice that."""
    return [
        {"total_project_cost": str(kwh * per_kwh * (1 + i / n)), "installed_energy_storage_kwhac": str(kwh)}
        for i in range(n)
    ]


def test_storage_percentiles_are_ordered_and_need_enough_projects():
    out = storage_percentiles(_storage_rows(40))
    assert out["p25_usd_per_kwh"] < out["p50_usd_per_kwh"] < out["p75_usd_per_kwh"] and out["projects"] == 40
    assert storage_percentiles(_storage_rows(5)) is None
    assert storage_percentiles(_storage_rows(30) + [{"total_project_cost": "0", "installed_energy_storage_kwhac": "5"}, {}])["projects"] == 30


def test_battery_price_appears_in_the_bill_and_the_assumption():
    priced = _inp(
        scenario_id="C", battery_kwh=500, critical_load_kw=60,
        battery_usd_per_kwh_low=530.0, battery_usd_per_kwh_high=800.0, battery_price_basis="NYSERDA storage test",
    )
    data = run_financial_model(priced).data
    battery = [i for i in data["cost_items"] if i["item"] == "Backup battery"][0]
    assert "$530-800/kWh" in battery["basis"] and "NYSERDA storage test" in battery["basis"]
    assert "NYSERDA storage test" in data["assumption_text"]


def test_live_mode_fills_battery_price_or_flags_the_placeholder(monkeypatch):
    found = {"p25_usd_per_kwh": 533, "p75_usd_per_kwh": 800, "projects": 69, "source_url": "https://data.ny.gov/s"}
    monkeypatch.setattr(solar_costs, "fetch_storage_cost_range", lambda: found)
    monkeypatch.setattr(solar_costs, "fetch_solar_cost_range", lambda kw: None)
    with forced_tool_mode("live"):
        updated, flags = _with_real_solar_price(_inp(scenario_id="C", battery_kwh=500, critical_load_kw=60))
    assert updated.battery_usd_per_kwh_low == 533 and updated.battery_usd_per_kwh_high == 800
    assert updated.battery_price_source_url == "https://data.ny.gov/s"
    assert flags == ["solar_price_placeholder"]  # solar had no data here, battery did

    monkeypatch.setattr(solar_costs, "fetch_storage_cost_range", lambda: None)
    with forced_tool_mode("live"):
        same, flags = _with_real_solar_price(_inp(scenario_id="C", battery_kwh=500, critical_load_kw=60))
    assert same.battery_usd_per_kwh_low is None and "battery_price_placeholder" in flags


def test_no_battery_lookup_when_the_scenario_has_no_battery(monkeypatch):
    def boom():
        raise AssertionError("should not be called")

    monkeypatch.setattr(solar_costs, "fetch_storage_cost_range", boom)
    monkeypatch.setattr(solar_costs, "fetch_solar_cost_range", lambda kw: None)
    with forced_tool_mode("live"):
        _with_real_solar_price(_inp())
