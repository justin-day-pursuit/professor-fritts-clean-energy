"""
The plan opens with one plain-words answer, and the code checks it before it can be shown.

These use small made-up plans and notes, with no network and no Claude. The rules: a live run must have one; it must be the
right length; it may not promise savings, use internal names, or state a number the plan's own statements do not contain; and
it must mention a mismatch with the city's record, or the reason solar was turned down by the roof rules, when those happened.
"""

from __future__ import annotations

from agent.checks import PLAIN_ANSWER_MAX_WORDS, _number_values, _plain_answer_issues, run_check4
from agent.claims import Claim, RoadmapPayload, RoadmapSection
from agent.notes import AgentNotes
from agent.plan_summary import build_plan_summary
from agent.roadmap import render_roadmap_markdown

GOOD = (
    "You asked how to cut grid power another 30% by 2030 on a $400,000 budget. The plan finds the goal cannot be reached with "
    "what it could price. The building already has a solar array that fills its usable roof, so no new solar fits, and the "
    "grid use shown is what is left after that solar. That leaves efficiency such as lighting and controls, which the plan "
    "estimates would cut grid use by about 6 to 18 percent for roughly $40,000 to $137,000. That is inside your budget but "
    "only part of the way to the goal. Before relying on this, confirm the size and ownership of the existing array."
)


def _claim(text: str, low: float | None = None, high: float | None = None) -> Claim:
    """A labelled claim, with a value range when given."""
    extra = {"value_low": low, "value_high": high, "units": "USD"} if low is not None else {}
    return Claim(label="ESTIMATE", text=text, confidence="medium", calc_id="C1", **extra)


def _plan(answer: str = GOOD) -> RoadmapPayload:
    """A tiny plan whose statements contain the numbers GOOD uses."""
    section = RoadmapSection(
        section_id="1",
        title="Summary",
        claims=[
            _claim("Efficiency alone is estimated to cut grid use by about 6% to 18% for about $39,800 to $136,600.", 39_800, 136_600),
            _claim("The goal is a 30% cut by 2030 on a $400,000 capital budget."),
        ],
    )
    return RoadmapPayload(sections=[section], plain_answer=answer)


# ----------------------------------------------------------------------------------------------------------- presence


def test_a_live_run_without_a_plain_answer_is_sent_back():
    issues = _plain_answer_issues(_plan(""), None, required=True)
    assert len(issues) == 1 and "no plain-words answer" in issues[0]


def test_a_recorded_plan_without_one_is_left_alone():
    assert _plain_answer_issues(_plan(""), None, required=False) == []


def test_a_good_answer_passes():
    assert _plain_answer_issues(_plan(), AgentNotes(), required=True) == []


# ----------------------------------------------------------------------------------------------------------------- length


def test_a_one_line_answer_is_too_short():
    issues = _plain_answer_issues(_plan("The goal cannot be reached."), None, required=True)
    assert any("words; it should be about" in issue for issue in issues)


def test_a_rambling_answer_is_too_long():
    issues = _plain_answer_issues(_plan("word " * (PLAIN_ANSWER_MAX_WORDS + 20)), None, required=True)
    assert any("words; it should be about" in issue for issue in issues)


# ---------------------------------------------------------------------------------------------------------------- wording


def test_a_promise_of_savings_is_rejected():
    text = GOOD + " The plan guarantee is that you will save money."
    assert any("Promise wording" in issue for issue in _plain_answer_issues(_plan(text), None, required=True))


def test_declining_to_promise_is_not_a_promise():
    text = GOOD + " The plan cannot guarantee savings."
    assert not any("Promise wording" in issue for issue in _plain_answer_issues(_plan(text), None, required=True))


def test_internal_names_and_ids_are_rejected():
    for bad in ("The roof_age_20_plus flag applies.", "See A7 for the assumption.", "Calculation C1 shows this."):
        issues = _plain_answer_issues(_plan(GOOD + " " + bad), None, required=True)
        assert any("internal name or id" in issue for issue in issues), bad


# ---------------------------------------------------------------------------------------------------------------- numbers


def test_numbers_are_read_the_way_people_write_them():
    assert _number_values("about $40k to $1.2 million, 226,605 kWh, by 2030, 6%") == [40_000.0, 1_200_000.0, 226_605.0, 6.0]


def test_rounded_numbers_that_the_plan_gives_are_accepted():
    # $40,000 for $39,800 and $137,000 for $136,600 are within a few percent.
    assert not any("not in the plan" in issue for issue in _plain_answer_issues(_plan(), None, required=True))


def test_a_number_the_plan_never_stated_is_rejected():
    text = GOOD.replace("$137,000", "$900,000")
    issues = _plain_answer_issues(_plan(text), None, required=True)
    assert any("not in the plan's statements" in issue and "900,000" in issue for issue in issues)


# ---------------------------------------------------------------------------------------------- what it must not leave out


def test_a_mismatch_with_the_city_record_must_be_mentioned():
    notes = AgentNotes(flags=["intake_mismatch:floor_area_sqft"])
    silent = GOOD.replace("confirm the size and ownership of the existing array", "confirm the lighting type")
    issues = _plain_answer_issues(_plan(silent), notes, required=True)
    assert any("differs from the city's record" in issue for issue in issues)
    mentioned = silent + " The floor area you entered differs from the city record."
    assert _plain_answer_issues(_plan(mentioned), notes, required=True) == []


def test_a_roof_rule_that_turned_solar_down_must_be_explained():
    refusal = (
        "The existing 380 kW array already uses the whole usable roof (about 338 kW estimated). "
        "There is no free roof for a new array; plan efficiency and say so."
    )
    notes = AgentNotes(failed_tools={"get_solar_production": refusal}, flags=["tool_error:get_solar_production"])
    silent = "You asked about cutting grid power by 30%. The plan estimates efficiency cuts about 6 to 18 percent for $40,000 to $137,000, within your $400,000 budget, so the goal is not reached. Confirm the lighting type and the tariff before relying on this plan, and have the roof checked by a professional."
    issues = _plain_answer_issues(_plan(silent), notes, required=True)
    assert any("why solar was not sized" in issue for issue in issues)
    assert not any("why solar was not sized" in issue for issue in _plain_answer_issues(_plan(), notes, required=True))


def test_a_lookup_that_truly_failed_adds_no_roof_requirement():
    notes = AgentNotes(failed_tools={"get_utility_rates": "The read operation timed out"}, flags=["tool_error:get_utility_rates"])
    assert not any("why solar was not sized" in issue for issue in _plain_answer_issues(_plan(), notes, required=True))


# ---------------------------------------------------------------------------------------------------------- the whole check


def _issues(result) -> list[str]:
    """The list of problems a check found (a check result is a dict with a "details" entry)."""
    return result["details"].get("issues", [])


def test_run_check4_asks_for_it_only_when_told_to():
    plan = _plan("")
    assert not any("plain-words" in issue for issue in _issues(run_check4(plan, require_all_sections=True)))
    required = run_check4(plan, require_all_sections=True, require_plain_answer=True)
    assert any("plain-words" in issue for issue in _issues(required))


def test_a_follow_up_answer_never_needs_one():
    plan = _plan("")
    result = run_check4(plan, require_all_sections=False, require_plain_answer=True)
    assert not any("plain-words" in issue for issue in _issues(result))


# --------------------------------------------------------------------------------------------------------- showing it


def test_the_written_plan_opens_with_it():
    markdown = render_roadmap_markdown(_plan())
    assert markdown.index("## In plain words") < markdown.index("## 1.")
    assert GOOD[:60] in markdown


def test_a_plan_without_one_prints_exactly_as_before():
    assert "In plain words" not in render_roadmap_markdown(_plan(""))


def test_the_summary_for_the_screen_carries_it(monkeypatch):
    class NoEvents:
        """A run's saved events: this run has none."""

        @staticmethod
        def order_by(_field):
            return []

        @staticmethod
        def all():
            return []

    class Run:
        events = NoEvents()

    output = {"roadmap": _plan().model_dump(), "notes": AgentNotes().model_dump()}
    assert build_plan_summary(Run(), output, [])["plain_answer"] == GOOD
    output["roadmap"] = _plan("").model_dump()
    assert build_plan_summary(Run(), output, [])["plain_answer"] is None
