"""Tests for the 'Who to contact' list: which official pages are chosen for which building (no network)."""

from agent.notes import AgentNotes
from agent.roadmap import render_next_steps, render_roadmap_markdown
from tools.next_steps import STEPS, next_steps_for


def _names(site, battery=False):
    return [s["name"] for s in next_steps_for(site, battery)]


def test_every_building_gets_the_core_offices():
    names = _names({})
    for needed in ("NYC Department of Buildings", "FDNY", "Con Edison: connecting solar to the grid", "NYSERDA NY-Sun"):
        assert needed in names
    assert not any("Parks" in n or "Landmarks" in n or "Flood" in n or "School" in n for n in names)


def test_a_public_school_is_sent_to_dcas_sca_and_public_schools():
    names = _names({"owner_agency": "doe"})
    assert "NYC School Construction Authority (SCA)" in names and "NYC Public Schools" in names
    assert any("DCAS" in n for n in names)


def test_site_conditions_add_their_own_offices():
    assert any("Parks" in n for n in _names({"parkland": True}))
    assert any("Landmarks" in n for n in _names({"landmark": True}))
    flood = _names({"flood_zone": "AE"})
    assert "NYC Flood Hazard Mapper" in flood and "FEMA Map Service Center" in flood
    assert "NYC Flood Hazard Mapper" not in _names({"flood_zone": "X"})
    assert any("Local Laws 92" in n for n in _names({"roof_age_20_plus": True}))


def test_battery_guide_only_when_a_plan_has_a_battery():
    assert not any("Storage" in n for n in _names({}))
    assert any("Storage" in n for n in _names({}, battery=True))


def test_notes_detect_a_battery_from_the_scenarios():
    notes = AgentNotes()
    notes.calculations["F-C"] = {"package": {"battery_kwh": 500}}
    assert any("Storage" in s["name"] for s in notes.next_steps())
    assert not any("Storage" in s["name"] for s in AgentNotes().next_steps())


def test_every_entry_has_a_web_address_and_a_reason():
    for step in STEPS:
        assert step.url.startswith("https://") and step.why


def test_markdown_lists_the_steps_with_links_and_contacts():
    from tests.test_v6_roof_and_budget import _plan

    steps = next_steps_for({"parkland": True})
    text = "\n".join(render_next_steps(steps))
    assert "[NYC Parks, Office of Construction Permits](https://www.nycgovparks.org/permits/construction/contact)" in text
    assert "(718) 760-6601" in text
    assert "## Who to contact and where to start" in render_roadmap_markdown(_plan(), None, steps)
    assert "Who to contact" not in render_roadmap_markdown(_plan(), None, None)
