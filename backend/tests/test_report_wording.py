"""
The "Please confirm first" list on the report: a roof rule saying no is not called a failed lookup, and solar already on the
roof is compared with the city's record.

These use plain sample data, with no network and no Claude.
"""

from __future__ import annotations

from agent.plan_summary import confirm_first
from tools.roof import plain_refusal

FULL_ROOF = (
    "The existing 380 kW array already uses the whole usable roof (about 338 kW estimated). "
    "There is no free roof for a new array; plan efficiency and say so."
)
PITCHED = (
    "The roof is not flat ('pitched'), so the usable area and array size cannot be estimated from the flat-roof defaults. "
    "Ask the user to have an engineer or a roofer verify the usable roof area."
)


# ------------------------------------------------------------------------------------- telling a refusal from a failure


def test_a_full_roof_is_said_in_plain_words():
    text = plain_refusal(FULL_ROOF)
    assert text == "No room for new solar: the 380 kW array already on the roof uses the whole usable roof, so this plan is efficiency only."


def test_a_pitched_roof_is_said_in_plain_words():
    text = plain_refusal(PITCHED)
    assert text is not None
    assert "not flat ('pitched')" in text
    assert "engineer or roofer" in text


def test_a_broken_lookup_is_not_mistaken_for_a_refusal():
    assert plain_refusal("The read operation timed out") is None
    assert plain_refusal("NYC Open Data error (HTTP 503).") is None
    assert plain_refusal("") is None
    assert plain_refusal(None) is None


# --------------------------------------------------------------------------------------------- the confirm-first list


def test_a_refusal_is_shown_as_its_reason_not_as_missing_data():
    reason = plain_refusal(FULL_ROOF)
    items = confirm_first(["tool_error:get_solar_production"], {}, {}, refusals={"get_solar_production": reason})
    texts = [item["text"] for item in items]
    assert reason in texts
    assert not any("could not return data" in text for text in texts)
    assert next(item for item in items if item["text"] == reason)["kind"] == "flag"


def test_a_failed_lookup_still_says_it_could_not_return_data():
    items = confirm_first(["tool_error:get_utility_rates"], {}, {})
    assert any("could not return data" in item["text"] for item in items)
    assert items[0]["kind"] == "gap"


def test_a_refusal_for_one_tool_does_not_hide_a_failure_of_another():
    reason = plain_refusal(PITCHED)
    items = confirm_first(
        ["tool_error:calculate", "tool_error:get_utility_rates"], {}, {}, refusals={"calculate": reason}
    )
    kinds = {item["text"]: item["kind"] for item in items}
    assert kinds[reason] == "flag"
    assert any(kind == "gap" for kind in kinds.values())


def test_solar_that_differs_from_the_city_record_is_listed_to_confirm():
    items = confirm_first([], {"ll24": {"installed_kw": 228.2, "status": "Completed"}}, {}, existing_solar_kw=380)
    text = next(item["text"] for item in items if item["kind"] == "mismatch")
    assert "You entered 380 kW" in text and "228.2 kW" in text


def test_solar_that_matches_the_city_record_is_not_flagged():
    assert confirm_first([], {"ll24": {"installed_kw": 380, "status": "Completed"}}, {}, existing_solar_kw=380) == []
    # A small difference (under 10%) is not worth the reader's attention.
    assert confirm_first([], {"ll24": {"installed_kw": 370, "status": "Completed"}}, {}, existing_solar_kw=380) == []


def test_planned_solar_in_the_city_record_is_not_compared_with_what_is_on_the_roof():
    assert confirm_first([], {"ll24": {"installed_kw": 219, "status": "In Progress"}}, {}, existing_solar_kw=380) == []


def test_no_comparison_is_made_when_either_side_is_missing():
    assert confirm_first([], {"ll24": {"installed_kw": 228.2, "status": "Completed"}}, {}, existing_solar_kw=None) == []
    assert confirm_first([], {"ll24": {"installed_kw": 0, "status": "Completed"}}, {}, existing_solar_kw=380) == []
    assert confirm_first([], {}, {}, existing_solar_kw=380) == []


def test_not_solar_ready_reads_differently_when_solar_is_already_installed():
    plain = confirm_first(["city_roof_not_solar_ready"], {}, {})
    installed = confirm_first(["city_roof_not_solar_ready"], {}, {}, existing_solar_kw=380)
    assert "consider replacing it" in plain[0]["text"]
    assert "yet solar is already installed" in installed[0]["text"]
    assert "consider replacing it" not in installed[0]["text"]


# ------------------------------------------------------------------- a failed try that is followed by a success


def test_a_tool_that_failed_once_and_then_worked_leaves_no_gap_flag():
    from agent.notes import AgentNotes
    from tools.base import ToolResult

    notes = AgentNotes()
    notes.record_tool_failure("get_solar_production", "A 337 kW array does not fit; send 109 or less.")
    assert "tool_error:get_solar_production" in notes.flags
    notes.record_tool_result("get_solar_production", ToolResult(tool="get_solar_production", data={"system_kw": 70}, source_url="https://example.test", retrieved_at="2026-10-18T00:00:00Z", mock=False))
    assert "tool_error:get_solar_production" not in notes.flags
    assert "get_solar_production" not in notes.failed_tools


def test_a_tool_that_never_worked_keeps_its_gap_flag():
    from agent.notes import AgentNotes

    notes = AgentNotes()
    notes.record_tool_failure("get_utility_rates", "The read operation timed out")
    assert "tool_error:get_utility_rates" in notes.flags
