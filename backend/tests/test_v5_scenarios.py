"""
Tests for v5: the simple financial model, the three scenarios (A, B, C), the battery sizing sample
and the full case 1 run. None of these call the network.

The numbers use Dana's Queens library (18,000 sq ft, 310,000 kWh a year, 400k budget, 50 kW roof array).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.claims import RoadmapPayload
from agent.coverage import check_coverage
from agent.notes import AgentNotes
from agent.scenarios import FinancialModelInput, run_financial_model
from tools.registry import execute_tool, list_tool_names

CASE = "case1_queens_library"


def _inputs(scenario_id: str, **overrides) -> FinancialModelInput:
    """Dana's site numbers for one scenario; each test changes only the field it is about."""
    base = dict(
        scenario_id=scenario_id,
        floor_area_sqft=18000,
        annual_use_kwh=310000,
        budget_usd=400000,
        full_array_kw_dc=50,
        annual_solar_kwh_low=55000,
        annual_solar_kwh_high=66000,
        price_low_usd_per_kwh=0.20,
        price_high_usd_per_kwh=0.24,
        battery_kwh=960 if scenario_id == "C" else 0,
        critical_load_kw=120,
    )
    base.update(overrides)
    return FinancialModelInput(**base)


def _run(scenario_id: str, **overrides) -> dict:
    """Run one scenario and return just its data dictionary."""
    return run_financial_model(_inputs(scenario_id, **overrides)).data


# --- the tool itself --------------------------------------------------------------------------


def test_tool_is_registered_and_runs_through_the_registry():
    """run_financial_model is on the approved list and the registry can execute it."""
    assert "run_financial_model" in list_tool_names()
    result = execute_tool(
        "run_financial_model",
        _inputs("A").model_dump(),
        session_profile={},
        fixture_case=CASE,
    )
    assert result.data["calc_id"] == "F-A"
    # Check 3 needs a retrieval time and a source on every result.
    assert result.retrieved_at and result.source_url


def test_scenario_a_is_efficiency_only():
    """A installs no solar and no battery, so it has no backup power and cuts 10-20% of use."""
    a = _run("A")
    assert a["package"]["solar_kw_dc"] == 0 and a["package"]["battery_kwh"] == 0
    assert a["reduction_pct_of_use"] == [10.0, 20.0]
    assert a["outage_hours"] == [0.0, 0.0]
    assert a["upfront_usd"] == [72000.0, 144000.0]  # 18,000 sq ft x $4-8


def test_scenario_b_stays_within_budget_and_is_capped_by_it():
    """B uses the whole array when the budget allows it, and a smaller one when it does not."""
    b = _run("B")
    assert b["package"]["solar_kw_dc"] == 50.0
    assert b["budget_strain"] == "within budget"
    assert b["upfront_usd"][1] <= 400000

    # With only 200k, efficiency (up to 144k) leaves 56k, which buys about 12 kW at the high price.
    tight = _run("B", budget_usd=200000)
    assert 0 < tight["package"]["solar_kw_dc"] < 50
    assert tight["upfront_usd"][1] <= 200000


def test_scenario_c_reaches_the_goal_with_a_battery_but_strains_the_budget():
    """C is the full path: it reaches 30%, gives backup hours, and costs far more than 400k."""
    c = _run("C")
    assert c["reaches_goal"] is True
    assert c["package"]["battery_kwh"] == 960
    # 960 kWh x 85-100% usable / 120 kW critical load = 6.8-8 hours.
    assert c["outage_hours"] == [6.8, 8.0]
    assert c["budget_strain"] == "over budget"


def test_no_incentive_is_counted_unless_the_program_is_confirmed_open():
    """Safe default: net cost equals upfront cost. Only federal_credit_open=True takes the 30% credit."""
    closed = _run("C")
    assert closed["incentives_counted_usd"] == [0.0, 0.0]
    assert closed["net_cost_usd"] == closed["upfront_usd"]

    opened = _run("C", federal_credit_open=True)
    assert opened["incentives_counted_usd"][1] > 0
    assert opened["net_cost_usd"][1] < opened["upfront_usd"][1]
    # The credit applies to solar and battery only, never to the efficiency work.
    assert opened["incentives_counted_usd"][0] == pytest.approx(0.30 * (50 * 3000 + 960 * 600))


def test_payback_is_a_range_and_every_result_is_an_estimate():
    """Payback runs from fast (low cost, high savings) to slow, and the label is always ESTIMATE."""
    a = _run("A")
    fast, slow = a["payback_years"]
    assert fast < slow
    assert fast == pytest.approx(72000 / 14880, abs=0.1)
    assert a["label"] == "ESTIMATE"


def test_solar_alone_is_about_15_to_25_percent_and_not_the_goal():
    """The v5 goalpost: whole-roof solar alone is flagged as short of the 30% goal."""
    data = _run("B")
    low, high = data["solar_alone_pct_of_use"]
    assert 15 <= low <= high <= 25
    assert data["solar_alone_reaches_goal"] is False


def test_bad_inputs_are_rejected():
    """Unknown scenarios, backwards ranges and a zero floor area fail with a clear message."""
    with pytest.raises(ValueError):
        run_financial_model(_inputs("Z"))
    with pytest.raises(ValueError):
        run_financial_model(_inputs("A", annual_solar_kwh_low=70000))
    with pytest.raises(ValidationError):
        _inputs("A", floor_area_sqft=0)


def test_no_budget_given_is_reported_not_guessed():
    """A budget of 0 means 'none given': strain says so and B installs no solar it cannot justify."""
    b = _run("B", budget_usd=0)
    assert b["budget_strain"] == "no budget given"
    assert b["package"]["solar_kw_dc"] == 0


# --- battery sizing sample --------------------------------------------------------------------


def test_storage_sample_gives_the_critical_load_the_model_needs():
    """The saved REopt sample includes critical_load_kw so outage hours can be computed."""
    result = execute_tool("optimize_solar_storage", {}, session_profile={}, fixture_case=CASE)
    assert result.mock is True
    assert result.data["battery_kwh"] == 960 and result.data["critical_load_kw"] == 120


# --- working notes ----------------------------------------------------------------------------


def test_notes_register_a9_and_keep_each_scenario():
    """After the tool runs, assumption A9 exists and F-A..F-C are findable in the notes digest."""
    notes = AgentNotes()
    for sid in "ABC":
        notes.record_tool_result("run_financial_model", run_financial_model(_inputs(sid)))
    assert "A9" in notes.assumptions and "benchmark" in notes.assumptions["A9"].lower()
    assert "F-A, F-B, F-C" in notes.summarize_for_llm()


# --- prompt and full case 1 -------------------------------------------------------------------


def test_prompt_names_the_scenarios_and_phases_0_to_5():
    """The prompt the harness loads (v3 or later) tells the model to use the tool and lists roadmap phases 0-5."""
    from agent.harness import load_system_prompt

    text = load_system_prompt()
    assert "run_financial_model" in text and "## Scenarios (v5)" in text
    phases = text.split("Section 8")[1][:700]
    for phase in range(6):
        assert f"{phase} " in phases


def test_case1_compares_three_scenarios_end_to_end(monkeypatch):
    """The v5 goalpost: case 1 in mock mode shows A, B and C on all six measures, fully labeled."""
    from django.conf import settings

    from agent.harness import run_harness
    from core import services
    from core.models import Run

    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("TOOL_MODE", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "scripted", raising=False)
    monkeypatch.setattr(settings, "TOOL_MODE", "mock", raising=False)

    profile = {
        "state": "NY",
        "borough": "Queens",
        "budget_amount": 400000,
        "address": "41-17 Main Street",
        "goal": "Cut grid electricity 30% by 2030",
        "annual_kwh": 310000,
    }
    session = services.create_session(profile=profile, fixture_case=CASE)
    run = run_harness(session, "How do we cut grid power 30% by 2030 on $400k?", llm_provider="scripted")
    run = services.get_run_with_events(run.pk)
    assert run.status == Run.Status.DONE

    md = run.output["markdown"]
    section6 = md.split("## 6.")[1].split("## 7.")[0]
    for sid in "ABC":
        assert f"Scenario {sid}" in section6 and f"plan {sid.lower()} costs and savings" in section6.lower()
    # The six comparison measures, in plain words, appear for every scenario.
    for word in ("of the 30% goal", "upfront cost", "net cost", "payback", "budget", "outage backup"):
        assert section6.count(word) >= 3
    assert "does not reach the 30% goal" in section6  # solar alone

    # Phases 0-5 and the resilience section are present.
    section8 = md.split("## 8.")[1].split("## 9.")[0]
    for phase in range(6):
        assert f"Phase {phase}" in section8
    assert "no backup power" in md.split("## 9.")[1].split("## 10.")[0]

    # Every number carries a label, a confidence and an id.
    payload = RoadmapPayload.model_validate(run.output["roadmap"])
    assert check_coverage(payload).complete


# --- review fixes (PR #12 comments) -----------------------------------------------------------


def test_scenario_c_without_a_battery_or_critical_load_is_rejected():
    """C must not silently report 0 outage hours: a missing battery or critical load is an error."""
    with pytest.raises(ValueError, match="optimize_solar_storage"):
        run_financial_model(_inputs("C", critical_load_kw=0))
    with pytest.raises(ValueError, match="optimize_solar_storage"):
        run_financial_model(_inputs("C", battery_kwh=0))
    # A and B never need a battery, so a zero critical load is fine for them.
    assert _run("A", critical_load_kw=0)["outage_hours"] == [0.0, 0.0]


def test_prompt_lets_the_model_cite_both_calculate_and_scenario_ids():
    """The labels rule must not forbid the F-A/F-B/F-C ids the scenarios section requires."""
    from agent.harness import load_system_prompt

    text = load_system_prompt()
    rule = text.split("Only cite a `source_url`")[1].split("\n")[0]
    assert "run_financial_model" in rule and "F-A" in rule


def test_case2_has_a_storage_sample_so_a_live_model_run_does_not_fail():
    """Case 2 once had no optimize_solar_storage fixture, so a non-scripted mock run broke on that call."""
    result = execute_tool("optimize_solar_storage", {}, session_profile={}, fixture_case="case2_bronx_school")
    assert result.mock is True
    assert result.data["battery_kwh"] > 0 and result.data["critical_load_kw"] > 0
