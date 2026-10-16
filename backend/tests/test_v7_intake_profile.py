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
