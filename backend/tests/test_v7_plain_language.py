"""Tests for plain-language reporting: no ids, flag names or team words in what a manager reads (no network)."""

from agent.checks import run_check4
from agent.notes import AgentNotes
from agent.plain_names import CALCULATION_NAMES, calculation_formula, calculation_name, strip_id_prefix
from agent.roadmap import render_roadmap_markdown
from tests.test_v6_roof_and_budget import _claim, _plan


def _issues(plan, plain=True):
    """Check 4 issues for a plan, with the live-run plain-language rule on or off."""
    return run_check4(plan, notes=AgentNotes(), plain_language=plain).get("details", {}).get("issues") or []


def test_calculation_ids_have_plain_names_and_formulas():
    assert calculation_name("C1") == "Usable roof area" and calculation_name("F-B") == "Plan B costs and savings"
    assert calculation_name("Z9") == "Z9"
    assert calculation_formula("C3") and "Yearly solar output" in calculation_formula("C3")
    assert all(calculation_formula(k) for k in CALCULATION_NAMES)


def test_an_assumption_sentence_loses_its_id_prefix():
    assert strip_id_prefix("A7: Efficiency measures save 10-20%.") == "Efficiency measures save 10-20%."
    assert strip_id_prefix("A12 - Something.") == "Something."
    assert strip_id_prefix("Plain sentence about A7 in the middle.") == "Plain sentence about A7 in the middle."


def test_the_markdown_shows_names_not_ids():
    plan = _plan(
        s5=[_claim("Usable roof is about 5,643 sq ft.", label="ESTIMATE", calc_id="C1", source_url=None)],
        s3=[_claim("A4: Critical load is estimated.", label="ASSUMPTION", assumption_id="A4", source_url=None)],
    )
    md = render_roadmap_markdown(plan)
    assert "from the usable roof area" in md and "`C1`" not in md
    assert "A4:" not in md and "[A4]" not in md and "Critical load is estimated." in md


def test_a_live_plan_cannot_use_flag_names_ids_or_team_words():
    bad_flag = _plan(s12=[_claim("Flag city_roof_not_solar_ready: the city says the roof is not ready.", label="FACT")])
    assert any("Internal field or flag name" in i for i in _issues(bad_flag))
    bad_id = _plan(s4=[_claim("This depends on the savings estimate (A7).", label="ESTIMATE", calc_id="F-A", source_url=None)])
    assert any("Internal id" in i for i in _issues(bad_id))
    bad_team = _plan(s4=[_claim("The savings are a team placeholder.", label="ASSUMPTION", assumption_id="A7", source_url=None)])
    assert any("planning estimate" in i for i in _issues(bad_team))


def test_plain_text_and_assumption_prefixes_pass_and_saved_recordings_are_exempt():
    plain = _plan(
        s4=[_claim("The savings figure is a planning estimate.", label="ESTIMATE", calc_id="F-A", source_url=None)],
        s3=[_claim("A7: Efficiency measures save 10-20% of annual use.", label="ASSUMPTION", assumption_id="A7", source_url=None)],
    )
    assert not any(i.startswith(("Internal", "Say 'planning estimate'")) for i in _issues(plain))
    old_style = _plan(s12=[_claim("Flag hazard_partial: only the flood zone was read (A7).", label="FACT")])
    assert not any(i.startswith("Internal") for i in _issues(old_style, plain=False))


def test_the_summary_carries_plain_names_and_flag_sentences():
    from agent.plan_summary import FLAG_TEXT

    # Built from a saved replay in test_v7_plan_summary; here only the constants are checked.
    assert "hazard_partial" in FLAG_TEXT and FLAG_TEXT["hazard_partial"][0].isupper()
