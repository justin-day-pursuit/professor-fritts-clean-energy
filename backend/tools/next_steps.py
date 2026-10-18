"""
Who to contact and where to start: a curated list of official NYC, State and utility pages (v7).

The plan's referrals say WHICH professional or office is needed ("a licensed electrician", "a Landmarks review").
This list says WHERE to go for each one: the agency's own page, why this building needs it, and a phone or email
only when the agency itself publishes one. Code picks the entries from what the run learned about the building
(owner, landmark, parkland, flood zone, roof condition, battery in a plan), so the list is the same for every user
in the same situation and Claude cannot invent a link or a phone number.

Every address was checked to load on Oct 16, 2026. Two sites (NYC Parks, NYSERDA) refuse automated requests but
open normally in a browser. Update an address here if an agency moves its page.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

# FEMA zones that mean a high-risk flood area; matches the flood rules in agent/checks.py.
HIGH_RISK_FLOOD_ZONES = frozenset({"A", "AE", "AH", "AO", "V", "VE"})


@dataclass(frozen=True)
class NextStep:
    """One place to go: what it is, when it applies, the page, why, and any contact the agency publishes."""

    name: str
    url: str
    why: str
    applies: Callable[[dict[str, Any], bool], bool]
    contact: str = ""


def _always(site: dict[str, Any], has_battery: bool) -> bool:
    return True


STEPS: tuple[NextStep, ...] = (
    NextStep(
        name="NYC Department of Education route: DCAS Energy Management",
        url="https://www.nyc.gov/site/dcas/agencies/energy-management.page",
        why="DCAS runs energy projects for city buildings; for a public school, start here before buying solar.",
        applies=lambda s, b: s.get("owner_agency") in ("doe", "other_city", "hhc", "nycha"),
    ),
    NextStep(
        name="NYC School Construction Authority (SCA)",
        url="https://www.nycsca.org/",
        why="The SCA builds and repairs public school buildings, including roofs; roof work and solar on a school go through it.",
        applies=lambda s, b: s.get("owner_agency") == "doe",
    ),
    NextStep(
        name="NYC Public Schools",
        url="https://www.schools.nyc.gov/",
        why="The school system's facilities staff approve changes to a school building.",
        applies=lambda s, b: s.get("owner_agency") == "doe",
    ),
    NextStep(
        name="NYC Parks, Office of Construction Permits",
        url="https://www.nycgovparks.org/permits/construction/contact",
        why="Work on parkland needs a Parks construction permit; the office offers an informal plan review during planning.",
        contact="Capital Projects Division: (718) 760-6601",
        applies=lambda s, b: bool(s.get("parkland")),
    ),
    NextStep(
        name="NYC Landmarks Preservation Commission (LPC) applications",
        url="https://www.nyc.gov/site/lpc/applications/applications.page",
        why="A landmark or a building in a historic district needs LPC approval before rooftop or exterior work.",
        applies=lambda s, b: bool(s.get("landmark")),
    ),
    NextStep(
        name="NYC Flood Hazard Mapper",
        url="https://www.nyc.gov/site/planning/data-maps/flood-hazard-mapper.page",
        why="Shows the flood zone for the building, including the preliminary map NYC code also considers.",
        applies=lambda s, b: str(s.get("flood_zone") or "").upper() in HIGH_RISK_FLOOD_ZONES,
    ),
    NextStep(
        name="FEMA Map Service Center",
        url="https://msc.fema.gov/portal/home",
        why="FEMA's own flood maps, to confirm the zone before placing a battery or electrical equipment.",
        applies=lambda s, b: str(s.get("flood_zone") or "").upper() in HIGH_RISK_FLOOD_ZONES,
    ),
    NextStep(
        name="NYC Department of Buildings: Local Laws 92 and 94 (solar and green roofs)",
        url="https://www.nyc.gov/site/buildings/codes/ll92-solar-green-roofs.page",
        why="Replacing a roof triggers a rule to cover it with solar, a green roof, or both; plan the roof and solar together.",
        applies=lambda s, b: bool(s.get("roof_condition") == "poor" or s.get("roof_age_20_plus") or s.get("city_not_solar_ready")),
    ),
    NextStep(
        name="Con Edison: connecting solar to the grid",
        url="https://www.coned.com/en/save-money/using-distributed-generation-energy-sources/solar-energy/information-for-contractors",
        why="Every solar array needs a Con Edison interconnection application (a small or a large portal, depending on size).",
        contact="Con Edison Distributed Generation: dgexpert@coned.com",
        applies=_always,
    ),
    NextStep(
        name="Con Edison Solar Photovoltaics Guide (PDF)",
        url="https://www.coned.com/-/media/files/coned/documents/save-energy-money/using-private-generation/solar-photovoltaics-guide.pdf",
        why="The utility's own steps, fees and timelines for connecting solar.",
        applies=_always,
    ),
    NextStep(
        name="Con Edison Energy Storage System Guide (PDF)",
        url="https://www.coned.com/-/media/files/coned/documents/save-energy-money/using-private-generation/specs-and-tariffs/energy-storage-guide.pdf",
        why="A battery has its own connection rules; this is the utility's guide for them.",
        applies=lambda s, b: b,
    ),
    NextStep(
        name="NYC Department of Buildings",
        url="https://www.nyc.gov/site/buildings/index.page",
        why="Permits for solar, batteries and roof work are filed here, by a registered design professional and a licensed electrician.",
        applies=_always,
    ),
    NextStep(
        name="FDNY",
        url="https://www.nyc.gov/site/fdny/index.page",
        why="Rooftop solar and battery systems must meet FDNY access and safety rules.",
        applies=_always,
    ),
    NextStep(
        name="NYSERDA NY-Sun",
        url="https://www.nyserda.ny.gov/All-Programs/NY-Sun",
        why="The State's solar incentive program; confirm whether a public building can use it before counting any incentive.",
        applies=_always,
    ),
    NextStep(
        name="NYC Accelerator",
        url="https://accelerator.nyc/",
        why="A city program that helps building owners with energy upgrades and compliance.",
        applies=_always,
    ),
)


def next_steps_for(site_context: dict[str, Any], has_battery: bool = False) -> list[dict[str, str]]:
    """
    The entries that apply to this building, in a fixed order, as dicts of name, url, why and contact.

    `site_context` is what the run's notes learned (owner_agency, parkland, landmark, flood_zone, roof facts);
    `has_battery` is True when any scenario includes a battery.
    """
    return [
        {"name": step.name, "url": step.url, "why": step.why, "contact": step.contact}
        for step in STEPS
        if step.applies(site_context, has_battery)
    ]
