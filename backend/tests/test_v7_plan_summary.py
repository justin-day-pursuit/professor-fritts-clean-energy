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


# ---------------------------------------------------------------------------------------- the pill: what it says and its colour


def _with_outage(scenario, hours):
    """The same scenario result, with the backup hours it gives (zero means no battery)."""
    return {**scenario, "outage_hours": list(hours)}


def test_a_yes_within_budget_is_green_when_nothing_else_needs_saying():
    outcome = decide_outcome([_with_outage(_scenario("B", 51, 67, True, "within budget"), (0, 0))], {}, 750000, "How do we cut grid power 30% on $750k?")
    assert (outcome["code"], outcome["tone"], outcome["label"]) == ("reached_within_budget", "good", "Goal reached within budget")


def test_a_yes_within_budget_comes_with_the_roof_first_when_the_city_rates_the_roof_badly():
    # The costs leave out replacing the roof, so the yes depends on the roof passing review. The roof is the step that comes first (blue).
    for roof in ({"city_not_solar_ready": True}, {"roof_condition": "poor"}, {"roof_age_20_plus": True}):
        outcome = decide_outcome([_scenario("B", 54, 70, True, "within budget")], roof, 600000)
        assert (outcome["code"], outcome["tone"]) == ("reached_roof_first", "next-step"), roof
        assert outcome["label"] == "Goal reached, roof review first"
        assert "if the roof passes review" in outcome["headline"] and "repairing or replacing the roof" in outcome["subhead"]


def test_a_yes_within_budget_says_there_is_no_backup_when_the_visitor_asked_for_it():
    asked = decide_outcome([_with_outage(_scenario("B", 51, 67, True, "within budget"), (0, 0))], {}, 750000, "Keep critical loads running in outages, on $750k?")
    assert (asked["code"], asked["tone"], asked["label"]) == ("reached_no_backup", "caution", "Goal reached, no backup yet")
    assert "no backup power" in asked["headline"]
    # Not asked: green. Asked, and the plan has a battery: green.
    assert decide_outcome([_with_outage(_scenario("B", 51, 67, True, "within budget"), (0, 0))], {}, 750000, "Cut grid power 30%?")["code"] == "reached_within_budget"
    assert decide_outcome([_with_outage(_scenario("C", 51, 67, True, "within budget"), (8, 9.4))], {}, 750000, "Keep the lights on in an outage?")["code"] == "reached_within_budget"


def test_the_roof_comes_before_the_backup_when_a_plan_has_both():
    outcome = decide_outcome([_with_outage(_scenario("B", 51, 67, True, "within budget"), (0, 0))], {"city_not_solar_ready": True}, 750000, "keep power on in an outage")
    assert outcome["code"] == "reached_roof_first"


def test_a_goal_that_costs_more_is_amber_when_it_may_run_over_and_red_when_it_does_over():
    may = decide_outcome([_scenario("C", 31, 46, True, "may exceed budget", (592000, 1083000), gap=[0, 283593])], {"city_not_solar_ready": True}, 800000)
    assert (may["code"], may["tone"], may["label"]) == ("reached_may_exceed", "caution", "Reachable, may run over budget")
    over = decide_outcome([_scenario("C", 37, 49, True, "over budget", (900000, 1400000), gap=[100000, 600000])], {}, 800000)
    assert (over["code"], over["tone"], over["label"]) == ("reached_over_budget", "bad", "Reachable, over budget")


def test_a_goal_that_is_only_possible_at_the_high_end_is_amber_within_budget_and_red_when_it_does_not_fit():
    within = decide_outcome([_scenario("B", 28, 42, False, "within budget")], {}, 800000)
    assert (within["code"], within["tone"], within["label"]) == ("close", "caution", "Goal possible, not guaranteed")
    # The Flushing Library case: what fits the budget gets 8-20%, the full path reaches 30% only at its best and may cost far more.
    scenarios = [_scenario("A", 6.2, 17.6, False, "within budget"), _scenario("B", 8.3, 19.9, False, "within budget"),
                 _scenario("C", 17, 30.4, False, "may exceed budget", (1248227, 2845721), gap=[0, 1345721])]
    out = decide_outcome(scenarios, {}, 1500000)
    assert (out["code"], out["tone"], out["label"], out["recommended"]) == ("not_within_budget", "bad", "Not within budget", "C")
    assert out["headline"].startswith("Not on your $1,500,000 budget.") and "8.3-19.9%" in out["headline"] and "$1.35M more" in out["headline"]


def test_nothing_reaching_the_goal_is_red():
    assert decide_outcome([_scenario("A", 6, 18, False, "within budget")], {}, 800000)["tone"] == "bad"


def test_the_roof_check_stays_blue_and_a_partial_plan_stays_amber():
    assert decide_outcome([], {"roof_kind": "non_flat"}, None)["tone"] == "next-step"
    assert decide_outcome([], {"roof_kind": "non_flat", "verified_usable_roof_sqft": 4000}, None)["tone"] == "caution"


@pytest.mark.parametrize("question", [
    "Keep critical loads running in outages, on $750k?",
    "How do we add a battery?",
    "We need backup power for the cooling center",
    "Keep the cooling running in outages",
])
def test_these_questions_ask_for_backup_power(question):
    from agent.plan_summary import asks_for_backup
    assert asks_for_backup(question)


@pytest.mark.parametrize("question", ["How can our school cut grid power 30% by 2030 on a $600k capital budget?", "", None])
def test_these_questions_do_not(question):
    from agent.plan_summary import asks_for_backup
    assert not asks_for_backup(question)
