"""Tests for the LL84 energy and LL24 roof providers and how the records tool and notes use them (no network)."""

import pytest

from agent.notes import AgentNotes
from tools import city_energy
from tools.city_energy import CityEnergyError, fetch_ll24, fetch_ll84, parse_ll24_row, parse_ll84_row
from tools.live_records import compare_energy_with_ll84

# Rows shaped like the real P.S. 236 records (Bronx, lot 2028510021) returned by NYC Open Data.
LL84_ROW = {
    "report_year": "2024",
    "property_name": "X173",
    "primary_property_type": "K-12 School",
    "largest_property_use_type_1": "43760",
    "site_eui_kbtu_ft": "57.6",
    "weather_normalized_site_eui": "Not Available",
    "energy_star_score": "69",
    "electricity_use_grid_purchase": "1558717.6",
    "electricity_use_grid_purchase_1": "456834",
    "natural_gas_use_kbtu": "893000",
    "fuel_oil_2_use_kbtu": "69276",
    "district_steam_use_kbtu": "Not Available",
    "year_built": "1994",
}
LL24_ROW = {
    "agency": "DOE",
    "site": "X173",
    "status": "Not Solar Ready",
    "solar_readiness_assessment": "No",
    "roof_condition": "Fair",
    "roof_age": "20 years or more",
    "year_of_report": "2024",
    "upfront_project_cost": "$4,200,000",
}


class _Reply:
    """A stand-in for an HTTP reply."""

    def __init__(self, rows, status=200):
        self._rows, self.status_code = rows, status

    def json(self):
        return self._rows


def test_ll84_row_keeps_measured_kwh_and_turns_gaps_into_none():
    out = parse_ll84_row(LL84_ROW)
    assert out["electricity_kwh"] == 456834
    assert out["weather_normalized_site_eui"] is None
    assert out["district_steam_kbtu"] is None
    assert out["energy_star_score"] == 69


def test_ll24_row_reads_agency_roof_and_readiness():
    out = parse_ll24_row(LL24_ROW)
    assert out["agency"] == "DOE"
    assert out["solar_ready"] is False
    assert out["roof_age"] == "20 years or more"
    assert out["upfront_project_cost_usd"] == 4200000


def test_fetch_returns_newest_row_or_none(monkeypatch):
    monkeypatch.setattr(city_energy, "get_with_retry", lambda *a, **k: _Reply([LL84_ROW]))
    assert fetch_ll84("2028510021")["report_year"] == 2024
    monkeypatch.setattr(city_energy, "get_with_retry", lambda *a, **k: _Reply([]))
    assert fetch_ll24("2028510021") is None


def test_http_error_becomes_city_energy_error(monkeypatch):
    monkeypatch.setattr(city_energy, "get_with_retry", lambda *a, **k: _Reply([], status=500))
    with pytest.raises(CityEnergyError):
        fetch_ll84("2028510021")


def test_typed_kwh_far_from_city_record_is_flagged():
    assert compare_energy_with_ll84({"annual_kwh": 200000}, 456834)["city_record"] == 456834
    assert compare_energy_with_ll84({"annual_kwh": 450000}, 456834) is None
    assert compare_energy_with_ll84({}, 456834) is None


def test_notes_take_the_citys_roof_and_owner_but_keep_user_answers():
    notes = AgentNotes()
    notes._record_city_records({"ll24": parse_ll24_row({**LL24_ROW, "roof_condition": "Between Fair and Poor"})})
    ctx = notes.site_context
    assert ctx["owner_agency"] == "doe" and ctx["roof_condition"] == "poor"
    assert ctx["roof_age_20_plus"] and ctx["city_not_solar_ready"]
    # The user's own answer wins when it was recorded first.
    notes = AgentNotes()
    notes.site_context["roof_condition"] = "good"
    notes._record_city_records({"ll24": parse_ll24_row(LL24_ROW)})
    assert notes.site_context["roof_condition"] == "good"


def test_old_roof_from_city_record_requires_reroof_mention():
    from tests.test_v6_roof_and_budget import _claim, _issues, _plan

    notes = AgentNotes()
    notes.site_context["roof_age_20_plus"] = True
    assert any("20 years old or more" in i for i in _issues(_plan(), notes))
    ok = _plan(s5=[_claim("The roof is 20 years old, so plan a roof replacement before solar.")])
    assert not any("20 years old or more" in i for i in _issues(ok, notes))
