"""
Tests for v2: claim ranges, the 13-section renderer, the assumptions register, the coverage
script, missing-field flags and the mock tariff tool. None of these call the network.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.claims import SECTION_TITLES, Claim, RoadmapPayload, RoadmapSection
from agent.coverage import check_coverage
from agent.roadmap import build_assumptions_register, render_roadmap_markdown
from tools.building_records import find_missing_profile_fields, get_building_profile
from tools.registry import execute_tool


def _claim(**overrides) -> Claim:
    """A valid FACT claim; each test changes only the field it is about."""
    base = dict(text="Roof is flat.", label="FACT", confidence="high", source_url="session://profile")
    base.update(overrides)
    return Claim(**base)


# --- claim ranges -----------------------------------------------------------------------------


def test_range_needs_both_ends_and_units():
    """A range with only one end, backwards ends, or no unit is rejected."""
    with pytest.raises(ValidationError):
        _claim(value_low=1.0)
    with pytest.raises(ValidationError):
        _claim(value_low=5.0, value_high=1.0, units="kWh")
    with pytest.raises(ValidationError):
        _claim(value_low=1.0, value_high=2.0)
    assert _claim(value_low=1.0, value_high=2.0, units="kWh").units == "kWh"


# --- 13-section renderer ----------------------------------------------------------------------


def test_empty_plan_still_prints_all_13_sections_in_order():
    """Even with no sections at all, the plan lists 1-13 in order, each marked 'not provided'."""
    md = render_roadmap_markdown(RoadmapPayload(sections=[]))
    positions = [md.index(f"## {sid}. {title}") for sid, title in SECTION_TITLES.items()]
    assert positions == sorted(positions)
    assert md.count("Not provided in this run.") == 13


def test_renderer_uses_prd_titles_and_orders_sections():
    """Sections given out of order, with a custom title, still print in PRD order with PRD titles."""
    payload = RoadmapPayload(
        sections=[
            RoadmapSection(section_id="8", title="My own title", claims=[_claim(text="Do the survey.")]),
            RoadmapSection(section_id="1", title="Another title", claims=[_claim(text="Summary.")]),
        ]
    )
    md = render_roadmap_markdown(payload)
    assert md.index("## 1. Summary and goal status") < md.index("## 8. Priority roadmap")
    assert "My own title" not in md
    assert md.count("Not provided in this run.") == 11


def test_range_is_printed_with_units():
    """A claim's low/high shows up in the text as '55,000–66,000 kWh/yr'."""
    payload = RoadmapPayload(
        sections=[
            RoadmapSection(
                section_id="5",
                title="x",
                claims=[_claim(text="Solar output.", value_low=55000, value_high=66000, units="kWh/yr")],
            )
        ]
    )
    assert "55,000–66,000 kWh/yr" in render_roadmap_markdown(payload)


# --- assumptions register ---------------------------------------------------------------------


def test_register_lists_each_assumption_once_sorted_by_number():
    """A10 sorts after A2, and an id used in two sections appears only once."""
    def assumption(aid, text):
        return Claim(text=text, label="ASSUMPTION", confidence="low", assumption_id=aid)

    payload = RoadmapPayload(
        sections=[
            RoadmapSection(section_id="4", title="x", claims=[assumption("A10", "ten"), assumption("A2", "two")]),
            RoadmapSection(section_id="5", title="y", claims=[assumption("A2", "two again")]),
        ]
    )
    register = build_assumptions_register(payload)
    assert [c.assumption_id for c in register] == ["A2", "A10"]
    assert register[0].text == "two"
    md = render_roadmap_markdown(payload)
    # Section 3 is built from the register even though the model wrote nothing there.
    section3 = md.split("## 3.")[1].split("## 4.")[0]
    assert "two" in section3 and "ten" in section3 and "[A2]" not in section3  # ids stay in the data, not in the words


# --- coverage script --------------------------------------------------------------------------


def test_coverage_counts_only_numeric_claims_and_reports_gaps():
    """Word-only claims are ignored; a number with no id is reported as missing 'id'."""
    payload = RoadmapPayload(
        sections=[
            RoadmapSection(
                section_id="1",
                title="x",
                claims=[
                    _claim(text="No numbers here."),
                    _claim(text="Budget is 400000."),
                    Claim.model_construct(text="Savings 5000.", label="ESTIMATE", confidence="low"),
                ],
            )
        ]
    )
    report = check_coverage(payload)
    assert report.numeric_claims == 2
    assert report.covered == 1
    assert report.failures[0]["missing"] == ["id"]
    assert not report.complete


def test_empty_plan_is_not_counted_as_fully_covered():
    """With zero numbers there is nothing to vouch for, so the goalpost must not pass."""
    assert not check_coverage(RoadmapPayload(sections=[])).complete


# --- missing-field flags ----------------------------------------------------------------------


def test_missing_fields_are_listed_and_flagged():
    """Blank, None and 'unknown' count as missing; a real value and a 0 budget do not."""
    profile = {"address": "1 Main St", "borough": "", "budget_amount": 0, "roof_type": "unknown"}
    missing = find_missing_profile_fields(profile)
    assert "borough" in missing and "roof_type" in missing and "year_built" in missing
    assert "address" not in missing and "budget_amount" not in missing

    result = get_building_profile(profile)
    assert result.data["missing_fields"] == missing
    assert "missing_field:borough" in result.flags


def test_complete_intake_has_no_missing_flags():
    """Dana's full intake produces no missing_field flags."""
    import json
    from mocks.mock_mode import FIXTURES_ROOT

    intake = json.loads((FIXTURES_ROOT / "case1_queens_library" / "intake.json").read_text(encoding="utf-8"))
    assert get_building_profile(intake).flags == []


# --- tariff tool ------------------------------------------------------------------------------


def test_tariff_tool_returns_mock_tariff_for_confirmation():
    """The OpenEI stand-in is mock, carries provenance, and is flagged for user confirmation."""
    result = execute_tool("get_utility_tariff", {}, session_profile={}, fixture_case="case1_queens_library")
    assert result.mock is True
    assert result.source_url and result.retrieved_at and result.dataset_version
    assert result.data["tariff_name"].startswith("SC-9")
    assert "tariff_needs_user_confirmation" in result.flags


# --- the v2 goalpost, end to end --------------------------------------------------------------


def test_goalpost_command_passes_on_case1(monkeypatch):
    """Case 1 in mock mode returns all 13 sections and 100% of numbers covered (the v2 goalpost)."""
    from django.conf import settings
    from django.core.management import call_command

    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("TOOL_MODE", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "scripted", raising=False)
    monkeypatch.setattr(settings, "TOOL_MODE", "mock", raising=False)
    # The command exits non-zero (SystemExit) on failure, so simply running it is the assertion.
    call_command("check_coverage", case="case1_queens_library", llm="scripted")
