"""
Form pre-fill from free city records (v8).

Before the visitor reaches the energy and roof questions, the design page asks the backend what the city already
knows about the building: the yearly electricity it reported (Local Law 84), the city's own roof assessment and any
solar already installed or planned (Local Law 24), and a roof-area suggestion from the building outlines.

This module only turns those records into the short list of form values the page shows. It makes no web calls and
uses no Claude, so it can be tested with sample rows. Every value carries its source and a plain sentence for the
visitor, and every value is something they must confirm: nothing here is used by the planner on its own.
A record that is missing simply leaves its value out and says why in `missing`, so the form stays blank for that part.
"""

from __future__ import annotations

from typing import Any

from tools.city_energy import LL24_SOURCE_URL, LL84_SOURCE_URL
from tools.footprints import FOOTPRINTS_SOURCE_URL


def _item(field: str, label: str, value: Any, display: str, source: str, source_url: str, note: str) -> dict[str, Any]:
    """One value for the form: what it is, the number or text, how to show it, where it came from and what to keep in mind."""
    return {
        "field": field,
        "label": label,
        "value": value,
        "display": display,
        "source": source,
        "source_url": source_url,
        "note": note,
    }


def _positive(value: Any) -> float | None:
    """A number above zero, or None. The city files use 0 and blanks for 'not reported'."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def build_prefill(
    bbl: str,
    ll84: dict[str, Any] | None,
    ll24: dict[str, Any] | None,
    roof: dict[str, Any] | None,
    problems: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Make the pre-fill answer from whatever the three lookups found.

    `ll84`, `ll24` and `roof` are the results of the lookups (None when the city has nothing for the lot).
    `problems` says, by name ("energy", "roof_assessment", "roof_area"), which lookups could not be reached at all,
    so the page can tell "the city has no record" apart from "the city did not answer".
    """
    problems = problems or {}
    items: list[dict[str, Any]] = []
    missing: list[str] = []

    # Yearly electricity, from the building's own energy report to the city.
    kwh = _positive((ll84 or {}).get("electricity_kwh"))
    if kwh is not None:
        year = (ll84 or {}).get("report_year")
        when = f" for {year}" if year else ""
        items.append(
            _item(
                "annual_kwh",
                "Electricity used per year (kWh)",
                round(kwh),
                f"{round(kwh):,} kWh",
                f"NYC energy benchmarking report (Local Law 84){when}",
                LL84_SOURCE_URL,
                "This is the electricity the building reported to the city. A recent bill is more exact, so please check it.",
            )
        )
    elif "energy" in problems:
        missing.append("The city's energy reports did not answer, so yearly electricity use is blank. Type it, or attach a bill.")
    else:
        missing.append("The city has no energy report with electricity use for this building. Type it, or attach a bill.")

    # The city's own roof assessment and any solar already on the building.
    if ll24:
        condition = str(ll24.get("roof_condition") or "").strip()
        age = str(ll24.get("roof_age") or "").strip()
        year = ll24.get("report_year")
        when = f" ({year})" if year else ""
        source = f"City roof assessment (Local Law 24){when}"
        if condition:
            display = f"{condition}, roof age {age}" if age else condition
            items.append(
                _item(
                    "roof_condition",
                    "Roof condition (city assessment)",
                    condition,
                    display,
                    source,
                    LL24_SOURCE_URL,
                    "This is the city's own rating of its roof. A roofer should confirm before any design.",
                )
            )
        ready = bool(ll24.get("solar_ready"))
        items.append(
            _item(
                "solar_ready",
                "Roof ready for solar?",
                ready,
                "Rated solar ready by the city" if ready else "Not rated solar ready by the city",
                source,
                LL24_SOURCE_URL,
                "The city's assessment of whether the roof can take solar panels today.",
            )
        )
        installed = _positive(ll24.get("installed_kw"))
        if installed is not None:
            items.append(
                _item(
                    "existing_solar_kw",
                    "Solar already on the roof (kW)",
                    installed,
                    f"{installed:g} kW installed or planned",
                    source,
                    LL24_SOURCE_URL,
                    "The size the city lists as installed or planned. Please confirm what is actually on the roof.",
                )
            )
    elif "roof_assessment" in problems:
        missing.append("The city's roof assessments did not answer, so the roof condition is blank.")
    else:
        missing.append("The city has no roof assessment for this building, so the roof condition is blank.")

    # A roof-area suggestion from the building outlines on the lot.
    area = _positive((roof or {}).get("suggested_roof_area_sqft"))
    if area is not None:
        count = int((roof or {}).get("building_count") or 0)
        items.append(
            _item(
                "roof_area_sqft",
                "Roof area (sq ft)",
                round(area),
                f"About {round(area):,} sq ft",
                f"NYC building footprints ({count} outline{'s' if count != 1 else ''} on the lot)",
                (roof or {}).get("source_url") or FOOTPRINTS_SOURCE_URL,
                "This is the ground area of the building outlines on the lot, not a measured roof. An engineer or roofer should confirm the usable area before any design.",
            )
        )
    elif "roof_area" in problems:
        missing.append("The city's building outlines did not answer, so the roof area is blank.")
    else:
        missing.append("The city has no building outline for this lot, so the roof area is blank.")

    return {"bbl": bbl, "items": items, "missing": missing}
