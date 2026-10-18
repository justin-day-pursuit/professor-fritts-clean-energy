"""Tests for the live incentives check: the register is verified against its official pages (pages are faked)."""

from datetime import date

from mocks.mock_mode import forced_tool_mode
from tools import live_incentives
from tools.live_incentives import applies, load_register, page_text, quote_for, verify_program
from tools.ny_rules_rates import search_ny_incentives_and_rules

IRS_HTML = "<html><body><nav>Elective payment menu.</nav><p>Tax-exempt and governmental entities can benefit from certain clean energy investment and production credits using new options enabled by legislation enacted in 2022.</p><script>var x=1</script></body></html>"
STATUTE_HTML = "<p>The credit shall not apply to property placed in service after December 31, 2027.</p>"


def _fake_pages(monkeypatch, pages):
    """Make read_page answer from a dict of url -> html (or None for a blocked page)."""
    def read(url):
        html = pages.get(url)
        return (None, "the page answered HTTP 403, which blocks automated reading") if html is None else (page_text(html), "")
    monkeypatch.setattr(live_incentives, "read_page", read)


def _entry(**over):
    entry = {"id": "t", "name": "Test program", "applies_to": "all", "recorded_status": "open", "as_of": "2026-10-16",
             "status_note": "Note.", "source_url": "https://irs.example/p", "verify_phrases": ["elective payment", "governmental"],
             "quote_phrases": ["governmental entities", "credit"]}
    entry.update(over)
    return entry


def test_page_text_skips_scripts_and_quote_is_a_real_sentence():
    text = page_text(IRS_HTML)
    assert "var x" not in text
    assert quote_for(text, ["governmental entities", "credit"]).startswith("Tax-exempt and governmental entities")
    assert quote_for(text, ["nothing like this"]) == ""


def test_a_verified_page_keeps_the_recorded_status_and_a_real_quote(monkeypatch):
    _fake_pages(monkeypatch, {"https://irs.example/p": IRS_HTML})
    program = verify_program(_entry(), today=date(2026, 10, 17))
    assert program["status"] == "open" and "governmental entities" in program["quote"] and program["page_hash"]


def test_a_blocked_or_changed_page_becomes_uncertain_with_the_reason(monkeypatch):
    _fake_pages(monkeypatch, {"https://irs.example/p": None})
    blocked = verify_program(_entry())
    assert blocked["status"] == "uncertain" and "HTTP 403" in blocked["status_note"] and "quote" not in blocked
    _fake_pages(monkeypatch, {"https://irs.example/p": "<p>Nothing relevant here at all.</p>"})
    changed = verify_program(_entry())
    assert changed["status"] == "uncertain" and "no longer contains" in changed["status_note"]


def test_the_statute_page_is_checked_too(monkeypatch):
    entry = _entry(statute_url="https://law.example/s", statute_verify_phrases=["December 31, 2027"])
    _fake_pages(monkeypatch, {"https://irs.example/p": IRS_HTML, "https://law.example/s": STATUTE_HTML})
    assert verify_program(entry)["status"] == "open"
    _fake_pages(monkeypatch, {"https://irs.example/p": IRS_HTML, "https://law.example/s": "<p>Rewritten.</p>"})
    assert verify_program(entry)["status"] == "uncertain"


def test_a_passed_deadline_closes_the_program(monkeypatch):
    _fake_pages(monkeypatch, {"https://irs.example/p": IRS_HTML})
    program = verify_program(_entry(deadline="2027-12-31"), today=date(2028, 1, 2))
    assert program["status"] == "closed" and "deadline" in program["status_note"]
    assert verify_program(_entry(deadline="2027-12-31"), today=date(2027, 6, 1))["status"] == "open"


def test_a_page_that_blocks_programs_stays_uncertain_as_recorded(monkeypatch):
    _fake_pages(monkeypatch, {})
    program = verify_program(_entry(recorded_status="uncertain", verify_phrases=[], status_note="Blocked."))
    assert program["status"] == "uncertain" and program["status_note"] == "Blocked."


def test_school_programs_apply_only_to_schools():
    solar_schools = [e for e in load_register() if e["applies_to"] == "doe"][0]
    assert applies(solar_schools, {"owner_agency": "doe"}) and applies(solar_schools, {"building_type": "elementary school"})
    assert not applies(solar_schools, {"owner_agency": "parks", "building_type": "recreation center"})


def test_the_register_only_cites_official_pages_not_finders():
    for entry in load_register():
        for url in (entry["source_url"], entry.get("statute_url") or entry["source_url"]):
            assert "dsireusa" not in url and url.startswith("https://")


def test_live_mode_uses_the_register_and_mock_mode_the_fixture(monkeypatch):
    _fake_pages(monkeypatch, {})
    with forced_tool_mode("live"):
        live = search_ny_incentives_and_rules("case1_queens_library", {"owner_agency": "parks"})
    assert live.mock is False and live.dataset_version == "curated-register-live-verified"
    assert "incentive_status_uncertain" in live.flags
    with forced_tool_mode("mock"):
        saved = search_ny_incentives_and_rules("case1_queens_library", {})
    assert saved.mock is True
