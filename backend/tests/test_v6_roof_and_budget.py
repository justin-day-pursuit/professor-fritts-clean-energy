"""
Tests for the v6 roof, existing-systems and budget changes: the roof suggestion from city footprints, the
rule that a roof that is not flat is never sized like a flat one, solar already on the roof, surplus solar
and the budget gap in the financial model, and the Check 4 rules that go with them.

None of these call the network. The footprint lookups are faked with outlines of known size.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from django.conf import settings

from agent.checks import run_check4
from agent.claims import Claim, RoadmapPayload, RoadmapSection, roadmap_with_sections
from agent.notes import AgentNotes
from agent.scenarios import FinancialModelInput, run_financial_model
from tests.test_v6_hardening import _StubLLM, _stub_run
from agent.llm.base import LLMStep
from core.models import Run
from tools import footprints
from tools.building_records import find_missing_profile_fields
from tools.footprints import FootprintError, polygon_area_sqft, summarize_footprints
from tools.live_records import compare_roof_with_footprints
from tools.registry import execute_tool
from tools.roof import (
    RoofNotSizableError,
    check_new_array_fits,
    free_array_kw,
    roof_kind,
    usable_array_kw,
)

CASE = "case1_queens_library"


@pytest.fixture(autouse=True)
def mock_tools(monkeypatch):
    """Mock tools and the scripted model, so nothing here touches the network."""
    monkeypatch.setattr(settings, "TOOL_MODE", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "scripted")


# --- helpers ------------------------------------------------------------------------------------


def _rectangle(width_ft: float, depth_ft: float, lon: float = -73.99, lat: float = 40.73) -> list[list[float]]:
    """A closed ring of [longitude, latitude] points for a rectangle of the given size in feet."""
    import math

    dlon = width_ft / (364_567.2 * math.cos(math.radians(lat)))
    dlat = depth_ft / 364_567.2
    return [[lon, lat], [lon + dlon, lat], [lon + dlon, lat + dlat], [lon, lat + dlat], [lon, lat]]


def _row(width_ft: float, depth_ft: float, **extra: Any) -> dict[str, Any]:
    """One footprint row as NYC Open Data sends it, with the outline as a MultiPolygon."""
    row = {
        "base_bbl": "1000000001",
        "last_status_type": "Constructed",
        "height_roof": "30",
        "construction_year": "1950",
        "shape_area": "1",  # deliberately wrong: the area must come from the outline, not this column
        "the_geom": {"type": "MultiPolygon", "coordinates": [[_rectangle(width_ft, depth_ft)]]},
    }
    row.update(extra)
    return row


def _claim(text: str, **kw: Any) -> Claim:
    """A labeled RECOMMENDATION citing the intake, unless the test overrides the fields."""
    fields = {"label": "RECOMMENDATION", "confidence": "high", "source_url": "session://profile"}
    fields.update(kw)
    return Claim(text=text, **fields)


def _plan(**sections: list[Claim]) -> RoadmapPayload:
    """A 13-section plan with the standard referrals, plus any section given as s5=[...], s12=[...]."""
    referrals = [
        _claim("Licensed PE or RA structural analysis."),
        _claim("Roof condition survey."),
        _claim("NYC licensed electrician."),
        _claim("FDNY rooftop access review."),
        _claim("Con Edison interconnection review."),
    ]
    given = {key[1:]: claims for key, claims in sections.items()}
    given["10"] = referrals + given.get("10", [])
    return roadmap_with_sections([RoadmapSection(section_id=sid, title=sid, claims=c) for sid, c in given.items()])


def _issues(payload: RoadmapPayload, notes: AgentNotes) -> list[str]:
    """Check 4 issues for this plan and run context (an empty list means it passed)."""
    return run_check4(payload, notes=notes).get("details", {}).get("issues") or []


def _profile(**overrides: Any) -> dict[str, Any]:
    """Dana's intake (flat roof, 6,000 sq ft), with any field the test changes."""
    base = json.loads((settings.BASE_DIR / "mocks" / "fixtures" / CASE / "intake.json").read_text(encoding="utf-8"))
    base.update(overrides)
    return base


# --- the roof suggestion from building footprints -----------------------------------------------


def test_area_comes_from_the_outline_in_square_feet():
    """A 100 ft by 60 ft outline measures about 6,000 sq ft, whatever the shape_area column says."""
    area = polygon_area_sqft({"type": "Polygon", "coordinates": [_rectangle(100, 60)]})
    assert 5_950 < area < 6_050


def test_a_courtyard_is_taken_out_of_the_area():
    """A hole in the outline (a courtyard) is subtracted, so only roof is counted."""
    outer, hole = _rectangle(100, 100), _rectangle(20, 20, lon=-73.99 + 0.0001, lat=40.73 + 0.0001)
    area = polygon_area_sqft({"type": "Polygon", "coordinates": [outer, hole]})
    assert 9_500 < area < 9_700


def test_summary_counts_only_constructed_buildings_above_shed_size():
    """Demolished outlines and shed-sized structures are listed or skipped, and the total is rounded."""
    rows = [
        _row(100, 60),
        _row(50, 4),  # about 200 sq ft or less: a shed
        _row(100, 60, last_status_type="Demolition"),
    ]
    summary = summarize_footprints(rows)
    assert summary["building_count"] == 1
    assert 5_900 < summary["total_footprint_sqft"] < 6_100
    assert summary["suggested_roof_area_sqft"] % 10 == 0
    assert any(not b["counted"] for b in summary["buildings"])


class _FakeResponse:
    """Stands in for an httpx response."""

    def __init__(self, payload: Any, status_code: int = 200):
        self._payload, self.status_code = payload, status_code

    def json(self) -> Any:
        return self._payload


def test_footprint_lookup_adds_up_the_buildings_on_the_lot(monkeypatch):
    """Two buildings on one lot are added together, and the lot is queried by its BBL."""
    seen = {}

    def fake_get(url, **kwargs):
        seen["where"] = kwargs["params"]["$where"]
        return _FakeResponse([_row(100, 60), _row(100, 40)])

    monkeypatch.setattr(footprints, "get_with_retry", fake_get)
    summary = footprints.fetch_footprints("3005820001")
    assert seen["where"] == "base_bbl='3005820001'"
    assert summary["building_count"] == 2
    assert 9_900 < summary["total_footprint_sqft"] < 10_100


def test_footprint_lookup_with_no_outlines_says_so(monkeypatch):
    """A lot with no outlines raises a plain error, so the form tells the user to type the area."""
    monkeypatch.setattr(footprints, "get_with_retry", lambda url, **kw: _FakeResponse([]))
    with pytest.raises(FootprintError, match="No building footprints"):
        footprints.fetch_footprints("1")


def test_suggestion_endpoint_returns_the_suggestion_and_its_note(api_client, monkeypatch):
    """The form's helper endpoint returns the suggested area with its source and a warning that it is not a measured roof."""
    monkeypatch.setattr(
        footprints, "geocode_nyc_address", lambda address, borough: {"bbl": "3005820001", "label": "155 BAY STREET"}
    )
    monkeypatch.setattr(footprints, "get_with_retry", lambda url, **kw: _FakeResponse([_row(100, 60)]))
    body = api_client.get("/api/records/roof-suggestion", params={"address": "155 Bay Street", "borough": "Brooklyn"}).json()
    assert 5_900 < body["suggested_roof_area_sqft"] < 6_100
    assert body["source_url"].endswith("5zhs-2jue")
    assert "not a measured roof" in body["note"]


def test_suggestion_endpoint_reports_an_unknown_address(api_client, monkeypatch):
    """An address the city cannot place gives a 404 with the reason."""
    from tools.geocode import GeocodeError

    def no_match(address, borough):
        raise GeocodeError("The NYC geocoder found no match.")

    monkeypatch.setattr(footprints, "geocode_nyc_address", no_match)
    response = api_client.get("/api/records/roof-suggestion", params={"address": "999 Nowhere Street"})
    assert response.status_code == 404 and "no match" in response.json()["detail"]


def test_a_typed_roof_far_from_the_outlines_is_flagged_but_never_changed():
    """A roof 3x the outlines is flagged for confirmation; a roughly matching one is not."""
    assert compare_roof_with_footprints({"roof_area_sqft": 55000}, 17000) == {
        "field": "roof_area_sqft", "intake": 55000.0, "city_record": 17000,
    }
    assert compare_roof_with_footprints({"roof_area_sqft": 6000}, 7000) is None
    assert compare_roof_with_footprints({}, 7000) is None
    assert compare_roof_with_footprints({"roof_area_sqft": 6000}, None) is None


# --- a roof that is not flat is never sized like a flat one -------------------------------------


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("flat", "flat"), ("Flat roof", "flat"), ("low-slope", "flat"),
        ("pitched, with clock tower", "non_flat"), ("sloped", "non_flat"), ("mixed", "non_flat"),
        ("other", "non_flat"), ("flat with tower", "non_flat"), ("hipped", "non_flat"),
        ("", "unknown"), ("unknown", "unknown"), ("membrane", "unknown"), ("ship deck", "unknown"),
    ],
)
def test_roof_kind_reads_the_roof_type(text, kind):
    """Pitched, sloped, mixed and tower roofs are not flat; blank or unclear text is unknown, not guessed."""
    assert roof_kind(text) == kind


def test_solar_and_roof_formulas_refuse_a_pitched_roof_with_the_reason():
    """For a pitched roof, neither the solar tool nor C1 sizes anything, and the error says what the user must do."""
    profile = _profile(roof_type="pitched, with clock tower")
    with pytest.raises(RoofNotSizableError, match="engineer or a roofer"):
        execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)
    with pytest.raises(RoofNotSizableError, match="verified_usable_roof_sqft"):
        execute_tool(
            "calculate", {"formula": "C1", "inputs": {"roof_area_sqft": 6000}}, session_profile=profile, fixture_case=CASE
        )


def test_a_flat_or_unknown_roof_is_still_sized_as_before():
    """Flat roofs keep working exactly as before, and an unknown roof type is not blocked."""
    for roof in ("flat", ""):
        profile = _profile(roof_type=roof)
        result = execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)
        assert "pitched_roof_output_not_modeled" not in result.flags
        c1 = execute_tool("calculate", {"formula": "C1", "inputs": {"roof_area_sqft": 6000}}, session_profile=profile, fixture_case=CASE)
        assert c1.data["value"] == 3300


def test_a_verified_usable_area_unlocks_sizing_and_is_used_as_it_is():
    """With an engineer-verified area, C1 must use that number with no setback, and the output is flagged."""
    profile = _profile(roof_type="pitched", verified_usable_roof_sqft=2000)
    result = execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)
    assert "pitched_roof_output_not_modeled" in result.flags
    with pytest.raises(ValueError, match="setback_factor=1"):
        execute_tool("calculate", {"formula": "C1", "inputs": {"roof_area_sqft": 6000}}, session_profile=profile, fixture_case=CASE)
    c1 = execute_tool(
        "calculate",
        {"formula": "C1", "inputs": {"roof_area_sqft": 2000, "setback_factor": 1}},
        session_profile=profile,
        fixture_case=CASE,
    )
    assert c1.data["value"] == 2000


# --- solar already on the roof ------------------------------------------------------------------


def test_free_roof_is_the_whole_roof_minus_the_existing_array():
    """Dana's roof holds 50 kW; with 20 kW already installed, 30 kW is free, and never below zero."""
    assert usable_array_kw(_profile()) == pytest.approx(50)
    assert free_array_kw(_profile(existing_solar_kw=20)) == pytest.approx(30)
    assert free_array_kw(_profile(existing_solar_kw=80)) == 0


def test_an_array_that_does_not_fit_beside_the_existing_one_is_refused():
    """A 50 kW request next to 20 kW of existing solar is refused with the size that fits; 30 kW passes."""
    profile = _profile(existing_solar_kw=20)
    with pytest.raises(ValueError, match="send system_kw of 30 or less"):
        check_new_array_fits(profile, 50)
    check_new_array_fits(profile, 30)


def test_a_roof_already_full_of_solar_has_no_room_for_more():
    """When the existing array uses the whole roof, the solar tool says there is no free roof."""
    profile = _profile(existing_solar_kw=60)
    with pytest.raises(RoofNotSizableError, match="no free roof"):
        execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)


def test_solar_result_reports_the_free_capacity():
    """With existing solar, the solar result carries the existing size and the free capacity to plan with."""
    result = execute_tool("get_solar_production", {"system_kw": 25}, session_profile=_profile(existing_solar_kw=20), fixture_case=CASE)
    assert result.data["existing_solar_kw"] == 20 and result.data["free_capacity_kw"] == 30


def test_a_blank_existing_systems_section_is_a_missing_field_but_none_is_an_answer():
    """Leaving the whole section blank is flagged; "none", a number 0 or any listed system counts as answered."""
    blank = _profile(existing_renewables="", existing_efficiency="")
    assert "existing_systems" in find_missing_profile_fields(blank)
    for answer in ({"existing_renewables": "none"}, {"existing_solar_kw": 0}, {"existing_efficiency": "LED in 2021"}):
        profile = _profile(existing_renewables="", existing_efficiency="")
        profile.update(answer)
        assert "existing_systems" not in find_missing_profile_fields(profile)


def test_notes_remember_the_roof_kind_and_the_systems_the_building_has():
    """The notes keep the roof kind and a sentence of existing systems; "none" adds nothing."""
    notes = AgentNotes()
    profile = _profile(roof_type="pitched", existing_solar_kw=20, existing_solar_kwh=24000, existing_efficiency="LED lighting")
    notes.record_tool_result("get_building_profile", execute_tool("get_building_profile", {}, session_profile=profile, fixture_case=CASE))
    assert notes.site_context["roof_kind"] == "non_flat"
    assert "solar 20 kW" in notes.site_context["existing_systems"] and "LED" in notes.site_context["existing_systems"]
    plain = AgentNotes()
    plain.record_tool_result("get_building_profile", execute_tool("get_building_profile", {}, session_profile=_profile(), fixture_case=CASE))
    assert "existing_systems" not in plain.site_context


# --- surplus solar and the budget gap ------------------------------------------------------------


def _model(scenario: str, **overrides: Any) -> dict:
    """One scenario for a school whose roof out-produces its use (P.S. 38's numbers), as plain data."""
    base = dict(
        scenario_id=scenario, floor_area_sqft=55860, annual_use_kwh=284403, budget_usd=600000, full_array_kw_dc=458,
        annual_solar_kwh_low=541272, annual_solar_kwh_high=594828, price_low_usd_per_kwh=0.1981,
        price_high_usd_per_kwh=0.2418, battery_kwh=960 if scenario == "C" else 0, critical_load_kw=120,
    )
    base.update(overrides)
    return run_financial_model(FinancialModelInput(**base)).data


def test_a_reduction_never_goes_above_100_percent_of_use():
    """Solar beyond what the building uses is surplus: reduction stops at 100% and the surplus is reported, not credited."""
    c = _model("C")
    assert c["reduction_pct_of_use"] == [100.0, 100.0]
    assert c["surplus_solar_kwh"][0] > 0 and c["surplus_not_counted_in_savings"] is True
    assert c["annual_savings_usd"][1] <= 284403 * 0.2418 + 1  # savings never exceed the whole bill
    assert c["solar_alone_exceeds_use"] is True


def test_a_normal_case_has_no_surplus():
    """Dana's roof produces about 20% of her use, so nothing is surplus and the numbers are the same as before."""
    a = _model("B", floor_area_sqft=18000, annual_use_kwh=310000, budget_usd=400000, full_array_kw_dc=50,
               annual_solar_kwh_low=55000, annual_solar_kwh_high=66000, price_low_usd_per_kwh=0.20, price_high_usd_per_kwh=0.24)
    assert a["surplus_solar_kwh"] == [0.0, 0.0] and a["surplus_not_counted_in_savings"] is False
    assert a["reduction_pct_of_use"] == [27.7, 41.3]


def test_an_over_budget_scenario_states_the_gap_and_that_the_choice_is_the_users():
    """Scenario C reaches the goal but costs more than the budget; the note says by how much and leaves the choice open."""
    c = _model("C")
    low, high = c["budget_gap_usd"]
    assert high > low > 0
    assert "more than your budget" in c["budget_note"] and "extend" in c["budget_note"]
    a = _model("A")
    assert a["budget_gap_usd"] == [0.0, 0.0] and "fits within the budget" in a["budget_note"]


def test_no_budget_means_no_gap():
    """With no budget given, there is no gap to report and the note says budget strain was not assessed."""
    c = _model("C", budget_usd=0)
    assert c["budget_gap_usd"] is None and "No budget" in c["budget_note"]


# --- Check 4 rules for roof, existing systems, budget gap and calculation ids ----------------------


def test_a_pitched_roof_plan_must_tell_the_user_to_verify_the_roof():
    """Without a line about an engineer or roofer verifying the usable area, Check 4 rejects the plan; with it, it passes."""
    notes = AgentNotes(site_context={"roof_kind": "non_flat"})
    assert any("verify" in i for i in _issues(_plan(), notes))
    told = _plan(s5=[_claim("Have an engineer or roofer verify the usable roof area before any solar is designed.")])
    assert _issues(told, notes) == []


def test_no_solar_numbers_for_a_pitched_roof_until_it_is_verified():
    """A solar kWh figure for an unverified pitched roof is rejected; once an area is verified it is allowed."""
    plan = _plan(
        s5=[_claim("Have an engineer or roofer verify the usable roof area.")],
        s6=[_claim("The array would make about 60,000 kWh of solar power a year.")],
    )
    assert any("not flat and not verified" in i for i in _issues(plan, AgentNotes(site_context={"roof_kind": "non_flat"})))
    verified = AgentNotes(site_context={"roof_kind": "non_flat", "verified_usable_roof_sqft": 2000.0})
    assert not any("not flat and not verified" in i for i in _issues(plan, verified))


def test_existing_systems_must_be_acknowledged():
    """A plan that ignores solar the user said they already have is rejected; mentioning it in section 4 passes."""
    notes = AgentNotes(site_context={"existing_systems": "solar 20 kW"})
    assert any("existing systems" in i for i in _issues(_plan(), notes))
    ok = _plan(s4=[_claim("The existing 20 kW solar array is already counted in the grid baseline.")])
    assert _issues(ok, notes) == []


def _notes_with_over_budget_scenario() -> AgentNotes:
    """Notes that hold scenario C's result, which costs more than the budget."""
    notes = AgentNotes()
    notes.calculations["F-C"] = _model("C")
    return notes


def test_an_over_budget_scenario_must_be_called_out_in_the_plan():
    """Section 6 or 7 must say a scenario costs more than the budget; staying silent is rejected."""
    notes = _notes_with_over_budget_scenario()
    assert any("cost more than the budget" in i for i in _issues(_plan(), notes))
    said = _plan(s6=[_claim("Scenario C costs $1,900,000-$3,300,000 more than your budget but reaches the goal.", calc_id="F-C", source_url=None)])
    assert _issues(said, notes) == []


def test_a_cited_calculation_must_have_been_run():
    """A made-up calculation id, or a calculation the run never made, is rejected."""
    notes = AgentNotes()
    notes.calculations["C1"] = {"calc_id": "C1"}
    made_up = _plan(s5=[_claim("Roof area.", calc_id="C5", source_url=None)])
    assert any("C5" in i for i in _issues(made_up, notes))
    assert _issues(_plan(s5=[_claim("Roof area.", calc_id="C1", source_url=None)]), notes) == []


def test_a_scenario_claim_must_cite_its_own_scenario():
    """A sentence about Scenario B that cites F-A is rejected; a sentence about A and B may cite either."""
    notes = AgentNotes()
    notes.calculations.update({"F-A": {}, "F-B": {}})
    wrong = _plan(s6=[_claim("Scenario B costs more.", calc_id="F-A", source_url=None)])
    assert any("scenario B but cites F-A" in i for i in _issues(wrong, notes))
    both = _plan(s9=[_claim("Scenarios A and B give no backup power.", calc_id="F-A", source_url=None)])
    assert _issues(both, notes) == []


def test_a_landmark_on_parkland_must_say_the_lpc_gives_advice_not_a_permit():
    """On parkland the LPC review is advisory; section 10 that says "permit" without "advisory" is rejected."""
    notes = AgentNotes(site_context={"landmark": True, "parkland": True})
    permit = _plan(s10=[_claim("Landmarks Preservation Commission permit before work; parkland use review by counsel.")])
    assert any("advisory report" in i for i in _issues(permit, notes))
    advisory = _plan(s10=[_claim("The Landmarks Preservation Commission gives an advisory report; parkland use review by counsel.")])
    assert _issues(advisory, notes) == []


# --- a pitched roof through the whole harness -----------------------------------------------------


def test_a_pitched_roof_run_reports_the_refusal_and_asks_for_verification(monkeypatch):
    """Through the harness: the solar tool refuses a pitched roof, the model is told to ask for verification, and the failure is noted."""
    from core import services
    from agent import harness
    from agent.harness import run_harness

    stub = _StubLLM([LLMStep(kind="tool", tool_name="get_solar_production", tool_input={}, tool_use_id="t1")])
    monkeypatch.setattr(harness, "get_llm_client", lambda provider, fixture_case: stub)
    session = services.create_session(profile=_profile(roof_type="pitched, with clock tower"), fixture_case=CASE)
    run = run_harness(session, "Can we put solar on our roof?", llm_provider="anthropic", tool_mode="mock")
    run = services.get_run_with_events(run.pk)
    assert "engineer or a roofer" in stub.results[0]["error"]
    # The stub model has no more steps after the refusal, so the run ends without a plan, not with an invented one.
    assert run.status == Run.Status.FAILED and "roadmap" not in (run.output or {})
    errors = [e.payload for e in run.events.all() if e.kind == "error" and e.payload.get("tool")]
    assert errors and errors[0]["tool"] == "get_solar_production" and errors[0]["will_retry"] is True
    assert not [e for e in run.events.all() if e.kind == "tool_result"]  # no solar number was ever produced


# --- a false positive seen in the live P.S. 24 run (Oct 15, 2026) ---------------------------------


def test_the_users_own_existing_solar_numbers_are_not_invented_solar():
    """
    The live plan repeated the existing array's 457,512 kWh (the user's own number) and was rejected as
    an invented solar figure. Claims that cite the intake and speak of existing solar are now left alone, but a
    new production estimate for the same roof, or an existing-solar claim that cites a tool, is still rejected.
    """
    notes = AgentNotes(site_context={"existing_systems": "solar 380 kW"})
    notes.record_tool_failure("get_solar_production", "no free roof")
    gap = _claim("The solar production call was not made because there is no free roof; new solar output is missing.")
    users_own = _plan(
        s4=[_claim("The existing array is reported at about 457,512 kWh a year, already counted in the grid baseline.")],
        s12=[gap],
    )
    assert _issues(users_own, notes) == []
    invented = _plan(s5=[_claim("A new array would make about 60,000 kWh of solar power a year.")], s4=[_claim("The existing array is counted.")], s12=[gap])
    assert any("Solar production number" in i for i in _issues(invented, notes))
