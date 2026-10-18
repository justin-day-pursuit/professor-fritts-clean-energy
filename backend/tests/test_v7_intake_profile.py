"""Tests for the intake-form additions: profile tidying, bills, goal percent and optional fields (no Claude calls)."""

from agent.checks import run_check1
from agent.profile_prep import bills_total, effective_profile, merge_bills, normalize_profile
from agent.scenarios import FinancialModelInput
from tools.building_records import find_missing_optional_fields, get_building_profile
from tools.registry import _goal_fraction_from_profile


def _bills(months, kwh_each=1000):
    """A parsed_summary like the bills upload produces."""
    return {"type": "bills", "months": [{"month": f"m{i}", "kwh": kwh_each} for i in range(months)]}


def test_old_critical_load_hours_becomes_backup_hours():
    out = normalize_profile({"critical_load_hours": 8})
    assert out["backup_hours_wanted"] == 8


def test_new_backup_hours_wins_over_old_field():
    out = normalize_profile({"critical_load_hours": 8, "backup_hours_wanted": 24})
    assert out["backup_hours_wanted"] == 24


def test_blank_goal_is_written_from_goal_percent():
    out = normalize_profile({"goal_percent": 30, "target_year": 2030})
    assert out["goal"] == "Cut grid electricity use by 30% by 2030"


def test_typed_goal_is_not_overwritten():
    assert normalize_profile({"goal": "go green", "goal_percent": 30})["goal"] == "go green"


def test_goal_percent_alone_satisfies_check1():
    profile = {"state": "NY", "borough": "Bronx", "budget_amount": 500000, "goal_percent": 30}
    assert run_check1(effective_profile(profile, []), "plan")["passed"]


def test_twelve_months_of_bills_fill_blank_annual_use():
    out = merge_bills({}, [_bills(12)])
    assert out["annual_kwh"] == 12000
    assert out["annual_kwh_source"] == "bills"
    assert "annual_kwh_from_bills" in out["profile_flags"]


def test_short_bills_are_flagged_and_not_scaled_up():
    out = merge_bills({}, [_bills(5)])
    assert "annual_kwh" not in out
    assert out["profile_flags"] == ["bills_incomplete:5_months"]


def test_typed_annual_use_is_kept_when_it_disagrees_with_bills():
    out = merge_bills({"annual_kwh": 20000}, [_bills(12)])
    assert out["annual_kwh"] == 20000
    assert any(f.startswith("annual_kwh_disagrees_with_bills") for f in out["profile_flags"])


def test_typed_annual_use_close_to_bills_raises_no_flag():
    assert merge_bills({"annual_kwh": 12500}, [_bills(12)])["profile_flags"] == []


def test_non_bill_documents_are_ignored():
    assert bills_total([{"status": "received"}, {}]) is None


def test_stored_profile_is_not_modified():
    stored = {"critical_load_hours": 8}
    effective_profile(stored, [_bills(12)])
    assert stored == {"critical_load_hours": 8}


def test_goal_percent_sets_goal_fraction():
    assert _goal_fraction_from_profile({"goal_percent": 40}) == 0.4
    assert _goal_fraction_from_profile({"goal_percent": ""}) is None
    assert _goal_fraction_from_profile({"goal_percent": 150}) is None
    assert FinancialModelInput.model_fields["goal_fraction"].default == 0.30


def test_optional_fields_are_listed_but_do_not_become_missing_flags():
    result = get_building_profile({"roof_condition": "unknown", "goal_percent": 30})
    assert "roof_condition" in result.data["optional_missing"]
    assert "goal_percent" not in result.data["optional_missing"]
    assert not any("roof_condition" in f for f in result.flags)
    assert "owner_agency" in find_missing_optional_fields({})


def test_profile_flags_reach_the_tool_result():
    result = get_building_profile({"profile_flags": ["annual_kwh_from_bills"]})
    assert "annual_kwh_from_bills" in result.flags


# ---- battery sizing from the user's own numbers ----

import pytest

from mocks.mock_mode import forced_tool_mode
from tools.base import ToolUnavailableError
from tools.solar_savings import optimize_solar_storage, size_battery_from_profile


def test_battery_sized_from_users_kw_and_hours():
    result = size_battery_from_profile({"critical_load_kw": 50, "backup_hours_wanted": 8})
    assert result.data["battery_kw"] == 50
    assert result.data["battery_kwh"] == round(50 * 8 / 0.85)
    assert result.mock is False
    assert result.flags == []


def test_blank_inputs_are_estimated_and_flagged():
    result = size_battery_from_profile({"floor_area_sqft": 40000})
    assert result.data["battery_kw"] == 40.0
    assert result.data["critical_load_hours"] == 8
    assert "battery_inputs_estimated" in result.flags
    assert "not metered" in result.data["notes"]


def test_nothing_to_size_from_is_unavailable_not_invented():
    with pytest.raises(ToolUnavailableError):
        size_battery_from_profile({})


def test_mock_mode_still_returns_the_saved_sample():
    with forced_tool_mode("mock"):
        result = optimize_solar_storage("case1_queens_library", {"critical_load_kw": 5})
    assert result.mock is True
    assert result.data["battery_kwh"] == 960


def test_live_mode_uses_the_profile():
    with forced_tool_mode("live"):
        result = optimize_solar_storage("case1_queens_library", {"critical_load_kw": 10, "backup_hours_wanted": 4})
    assert result.data["battery_kwh"] == round(10 * 4 / 0.85)


# ---- Check 4 rules for the optional intake answers ----

from agent.notes import AgentNotes
from tests.test_v6_roof_and_budget import _claim, _issues, _plan


def _site(**site):
    """Notes whose site context holds the given answers, as if the profile had been read."""
    notes = AgentNotes()
    notes.site_context.update(site)
    return notes


def test_skipped_questions_add_no_requirement():
    assert _issues(_plan(), _site()) == []


def test_notes_keep_real_answers_and_skip_unknown():
    notes = AgentNotes()
    notes._record_intake_details({"owner_agency": "doe", "roof_condition": "unknown", "heating_fuel": "oil"})
    assert notes.site_context == {"owner_agency": "doe", "heating_fuel": "oil"}


def test_parks_owner_marks_parkland():
    notes = AgentNotes()
    notes._record_intake_details({"owner_agency": "parks"})
    assert notes.site_context["parkland"] is True


def test_led_cannot_be_recommended_when_all_lighting_is_led():
    notes = _site(lighting_type="led_all")
    bad = _plan(s8=[_claim("Replace lighting with LED fixtures in phase 1.")])
    assert any("LED lighting recommended" in i for i in _issues(bad, notes))
    ok = _plan(s8=[_claim("Lighting is already LED, so no lighting upgrade is planned.")])
    assert not any("LED lighting recommended" in i for i in _issues(ok, notes))


def test_poor_roof_requires_a_reroof_mention():
    notes = _site(roof_condition="poor")
    assert any("roof is rated poor" in i for i in _issues(_plan(), notes))
    ok = _plan(s5=[_claim("The roof may need replacement before solar goes on.")])
    assert not any("roof is rated poor" in i for i in _issues(ok, notes))


def test_doe_owner_requires_the_school_route():
    notes = _site(owner_agency="doe")
    assert any("DOE school" in i for i in _issues(_plan(), notes))
    ok = _plan(s10=[_claim("Start with DCAS and NYC Public Schools.")])
    assert not any("DOE school" in i for i in _issues(ok, notes))


def test_non_electric_heating_must_be_called_out():
    notes = _site(heating_fuel="natural_gas")
    assert any("Heating is not electric" in i for i in _issues(_plan(), notes))
    ok = _plan(s4=[_claim("Heating runs on natural gas, which an electricity goal does not cover.")])
    assert not any("Heating is not electric" in i for i in _issues(ok, notes))
    assert _issues(_plan(), _site(heating_fuel="electric")) == []


def test_non_percent_goal_must_say_not_modeled():
    notes = _site(goal_type="resilience")
    assert any("not modeled" in i for i in _issues(_plan(), notes))
    ok = _plan(s1=[_claim("Your resilience goal is not modeled here, only a percent cut in electricity.")])
    assert not any("goal is not a percent" in i for i in _issues(ok, notes))


def test_annual_budget_limit_must_be_stated():
    notes = _site(budget_type_annual=True)
    assert any("budget is annual" in i for i in _issues(_plan(), notes))
    ok = _plan(s7=[_claim("Your budget is annual, but the model treats the amount as one total upfront figure.")])
    assert not any("budget is annual" in i for i in _issues(ok, notes))
