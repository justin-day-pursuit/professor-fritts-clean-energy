"""
Tests for the plan PDF: the plain-language cleaner, the number formats, and that the endpoint returns a real PDF.

The PDF is built from a small made-up plan summary (not a saved run), so these tests need no network, no database and no Claude.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from agent.plan_pdf import build_plan_pdf, money, money_range, number_range, pdf_filename, plainify, safe, split_headline
from api.main import create_app


def _summary() -> dict:
    """A small plan summary with the parts the PDF draws: an answer, one plan, one section, and a source."""
    return {
        "outcome": {
            "label": "Goal reachable, over budget",
            "headline": "Plan C reaches your 30% goal and could cost up to $284k more than your $800,000 budget.",
            "subhead": "Full path to the goal. Reaching the goal may take more than the amount set aside.",
            "recommended": "C",
        },
        "building": {"intake": {"building_name": "P.S. 236 Langston Hughes (DOE building X173)", "address": "1871 Walton Avenue", "borough": "Bronx"}},
        "confirm_first": [{"kind": "missing", "text": "Not given: the year the roof was last replaced. The plan states what it assumed."}],
        "scenarios": [
            {
                "scenario_id": "C",
                "goal_pct": 30.0,
                "package": {"efficiency_level": "deep", "solar_kw_dc": 85.5, "battery_kwh": 412.0},
                "upfront_usd": [592242.0, 1083593.0],
                "upfront_usd_best": 822708,
                "net_cost_usd": [444447.0, 863495.0],
                "incentives_counted_usd": [147795.0, 220098.0],
                "reduction_pct_of_use": [31.4, 46.3],
                "reaches_goal": True,
                "annual_savings_usd": [28444.0, 51165.0],
                "payback_years": [8.7, 30.4],
                "payback_years_best": 16.2,
                "outage_hours": [8.0, 9.4],
                "budget_note": "Reaches the goal, but the estimated cost is up to $283,593 more than your budget.",
            }
        ],
        "sections": [
            {
                "section_id": "3",
                "title": "Assumptions register",
                "claims": [
                    {
                        "text": "A7: Efficiency measures save 10-20% of annual use (team placeholder). It uses solar_kw_dc (C2).",
                        "label": "ASSUMPTION",
                        "confidence": "low",
                        "source_url": "https://example.org/source",
                    }
                ],
            }
        ],
        "sources": [{"label": "NYC PLUTO tax-lot record", "url": "https://data.cityofnewyork.us/x", "retrieved_at": "2026-10-17T07:31:55Z", "sample": False}],
    }


def test_plainify_removes_ids_flag_names_and_placeholder_wording():
    """Ids, code-style names and 'placeholder' never reach the reader, the same as on the plan page."""
    text = "A7: Efficiency measures save 10-20% of annual use (team placeholder). It uses solar_kw_dc (C2)."
    cleaned = plainify(text)
    assert "A7" not in cleaned and "C2" not in cleaned
    assert "solar kw dc" in cleaned
    assert "placeholder" not in cleaned.lower()
    assert "planning estimate" in cleaned


def test_number_formats_are_short_and_plain():
    """Money and ranges read the way the plan page writes them."""
    assert money(592242) == "$592k"
    assert money(1083593) == "$1.08M"
    assert money(823) == "$823"
    assert money_range([592242, 1083593]) == "$592k to $1.08M"
    assert number_range([8.7, 30.4], " years") == "9 to 30 years"
    assert number_range([31.4, 31.4], "%") == "31%"


def test_split_headline_takes_the_first_sentence():
    """A statement shows its first sentence in bold and the rest as reasoning."""
    assert split_headline("The roof is flat. It measures 10,000 sq ft.") == ("The roof is flat.", "It measures 10,000 sq ft.")
    assert split_headline("One sentence only.") == ("One sentence only.", "")


def test_safe_swaps_characters_the_pdf_font_cannot_draw():
    """An arrow or a not-equal sign must not become a black box in the file."""
    assert safe("a → b ≥ c") == "a to b &gt;= c"
    assert safe("5 < 6 & 7") == "5 &lt; 6 &amp; 7"


def test_the_pdf_is_a_real_file_with_a_sensible_name():
    """The bytes start like a PDF, and the name comes from the building."""
    pdf = build_plan_pdf(_summary())
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2000
    assert pdf_filename(_summary()) == "professor-fritts-plan-p-s-236-langston-hughes-doe-building-x173.pdf"


def test_an_empty_summary_still_builds_without_error():
    """A plan with almost nothing in it makes a short PDF instead of failing."""
    assert build_plan_pdf({"outcome": {"headline": "Nothing yet."}}).startswith(b"%PDF")


def test_endpoint_returns_a_pdf_download():
    """POST /api/plans/pdf answers with a PDF and a file name the browser can save it under."""
    client = TestClient(create_app())
    response = client.post("/api/plans/pdf", json={"plan_summary": _summary()})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert "professor-fritts-plan-" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_endpoint_rejects_something_that_is_not_a_plan():
    """A body with no answer and no sections is refused with a plain message."""
    client = TestClient(create_app())
    response = client.post("/api/plans/pdf", json={"plan_summary": {"hello": "world"}})
    assert response.status_code == 422
    assert "plan summary" in response.json()["detail"]


def _pdf_text(pdf: bytes) -> str:
    """All the text on every page of a PDF, read back with pypdf."""
    import io

    from pypdf import PdfReader

    return " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages)


def test_the_pdf_shows_the_plain_words_answer_under_the_headline_when_the_plan_has_one():
    summary = _summary()
    summary["plain_answer"] = "You asked how to cut grid power. The plan finds the goal can be reached, but not inside the budget."
    text = _pdf_text(build_plan_pdf(summary))
    assert "The plan finds the goal can be reached, but not inside the budget." in " ".join(text.split())


def test_a_plan_without_one_makes_the_same_pdf_as_before():
    assert "You asked" not in _pdf_text(build_plan_pdf(_summary()))
