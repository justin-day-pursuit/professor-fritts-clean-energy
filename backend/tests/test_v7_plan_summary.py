"""Tests for the plan summary: every finding is present, and the headline agrees with the numbers (no network)."""

import json
from pathlib import Path

import pytest
from django.conf import settings

from agent.plan_summary import FLAG_TEXT, confirm_first, decide_outcome
from core.models import Run

pytestmark = pytest.mark.django_db


def _scenario(sid, low, high, reaches, strain, upfront=(100000, 200000), gap=None):
    """A scenario result with only the fields the headline reads."""
    return {"scenario_id": sid, "scenario_name": f"Scenario {sid}", "goal_pct": 30.0, "reaches_goal": reaches,
            "reduction_pct_of_use": [low, high], "upfront_usd": list(upfront), "budget_strain": strain, "budget_gap_usd": gap}


def test_headline_goal_reached_within_budget_picks_the_cheapest():
    outcome = decide_outcome(
        [_scenario("B", 32, 44, True, "within budget", (300000, 700000)), _scenario("C", 37, 49, True, "within budget", (900000, 1400000))],
        {}, 800000)
    assert outcome["code"] == "reached_within_budget" and outcome["recommended"] == "B" and outcome["tone"] == "good"
    assert "$800,000" in outcome["headline"]


def test_headline_over_budget_close_and_not_reached():
    over = decide_outcome([_scenario("C", 37, 49, True, "over budget", (900000, 1400000), gap=[100000, 600000])], {}, 800000)
    assert over["code"] == "reached_over_budget" and "more than" in over["headline"]
    close = decide_outcome([_scenario("B", 28, 42, False, "within budget")], {}, 800000)
    assert close["code"] == "close"
    missed = decide_outcome([_scenario("A", 6, 18, False, "within budget")], {}, 800000)
    assert missed["code"] == "not_reached"


def test_a_roof_that_is_not_flat_needs_a_roofer_and_no_scenarios_is_partial():
    assert decide_outcome([], {"roof_kind": "non_flat"}, None)["code"] == "needs_roof_check"
    assert decide_outcome([], {"roof_kind": "non_flat", "verified_usable_roof_sqft": 4000}, None)["code"] == "partial"


def test_confirm_first_turns_flags_into_plain_sentences():
    records = {"differs_from_intake": [{"field": "floor_area_sqft", "intake": 55860, "city_record": 17620}]}
    items = confirm_first(["missing_field:roof_replaced_year", "intake_mismatch:floor_area_sqft", "battery_inputs_estimated", "tool_error:get_hazard_context", "unknown_flag"], records, {})
    texts = " ".join(i["text"] for i in items)
    assert "year the roof was last replaced" in texts and "55,860" in texts and "17,620" in texts
    assert FLAG_TEXT["battery_inputs_estimated"] in texts and "The flood-zone lookup could not return data" in texts and "Your floor area differs" in texts
    assert "unknown_flag" not in texts


def test_every_recorded_replay_carries_a_complete_summary():
    """Replaying a saved run (free) produces a summary with each part the screen needs."""
    from agent.harness import run_harness
    from core import services
    from mocks.catalog import load_case
    from mocks.mock_mode import forced_tool_mode

    profile, question = load_case("live_ps236_bronx_v7")
    session = services.create_session(profile=profile, fixture_case="live_ps236_bronx_v7")
    with forced_tool_mode("mock"):
        run = run_harness(session, question, llm_provider="scripted", tool_mode="mock")
    summary = run.output["plan_summary"]
    for key in ("outcome", "building", "baseline", "solar", "prices", "scenarios", "cost_basis", "incentives", "battery",
                "hazards", "calculations", "confirm_first", "assumptions", "referrals", "next_steps", "sources", "sections", "tools"):
        assert key in summary, key
    assert len(summary["scenarios"]) == 3 and summary["scenarios"][0]["cost_items"]
    assert summary["building"]["energy_report"]["electricity_kwh"] == 456834
    assert summary["baseline"]["goal_kwh"] == round(456834 * 0.30)
    assert len(summary["sections"]) == 13 and {c["calc_id"] for s in summary["sections"] for c in s["claims"] if c.get("calc_id")}
    assert summary["incentives"] and summary["calculations"].get("C1")
    # Each tool block keeps its data AND where it came from, so the screen never shows an empty block under a badge.
    for block in (summary["solar"]["production"], summary["prices"]["electricity"], summary["battery"], summary["hazards"]):
        assert block["data"] and block["source_url"] and block["retrieved_at"] and block["mock"] is not None
    assert summary["solar"]["production"]["tool"] == "get_solar_production"
    json.dumps(summary)  # the whole block must be plain JSON


def test_a_normal_plan_run_has_a_summary_and_no_error():
    from agent.harness import run_harness
    from core import services
    from mocks.catalog import load_case

    profile, question = load_case("case1_queens_library")
    session = services.create_session(profile=profile, fixture_case="case1_queens_library")
    run = run_harness(session, question, llm_provider="scripted", tool_mode="mock")
    assert "plan_summary" in run.output and "plan_summary_error" not in run.output


# ---- best guess in the headline, the user's own rate, and costs left out of the totals ----

def test_the_headline_leads_with_the_range_and_names_the_median_second():
    scenario = _scenario("B", 32, 44, True, "within budget", (300000, 700000))
    scenario["upfront_usd_best"] = 450000
    outcome = decide_outcome([scenario], {}, 800000)
    assert "$300k-$700k (the median of similar NYC projects is about $450k)" in outcome["subhead"]


def test_roof_replacement_is_listed_as_not_included_with_a_labeled_guide_figure():
    from agent.plan_summary import not_included

    items = not_included({"roof_area_sqft": 10260}, {"roof_age_20_plus": True})
    assert len(items) == 1 and items[0]["rough_guide_usd"] == [67000.0, 144000.0]  # 10,260 sq ft x $6.50 to $14
    assert "not audited" in items[0]["basis"] and "roofer" in items[0]["next"].lower()
    assert [g["url"] for g in items[0]["sources"]] == [
        "https://roofvista.com/resources/guides/nyc-flat-roof-replacement-guide",
        "https://roofobservations.com/new-york-roof-cost-guide/",
    ]
    assert not_included({"roof_area_sqft": 10260}, {}) == []
    assert "rough_guide_usd" not in not_included({}, {"roof_condition": "poor"})[0]
    flags = confirm_first([], {}, {"roof_age_20_plus": True})
    assert any("replacing the roof" in i["text"] for i in flags)


def test_a_price_the_user_entered_is_used_as_is_in_any_mode():
    from mocks.mock_mode import forced_tool_mode
    from tools.ny_rules_rates import get_utility_rates, user_electricity_rate

    assert user_electricity_rate({"electricity_rate_usd_per_kwh": "0.26"}) == 0.26
    assert user_electricity_rate({"electricity_rate_usd_per_kwh": 26}) is None  # cents by mistake: ignored, not guessed
    assert user_electricity_rate({}) is None
    for mode in ("mock", "live"):
        with forced_tool_mode(mode):
            result = get_utility_rates("case1_queens_library", {"electricity_rate_usd_per_kwh": 0.26})
        data = result.data
        assert result.mock is False and result.source_url == "session://profile"
        assert data["price_low_usd_per_kwh"] == data["price_high_usd_per_kwh"] == 0.26 and result.flags == []
