"""
A building's details from the city's free records, the way the website fills them in for a visitor.

When a visitor types an address and accepts the pre-filled form, the floor area and year built come from the city's tax-lot
file, the yearly electricity from the city's energy report, the roof area from the building outlines, and any completed solar
from the city's solar record. Nothing the visitor would have to type (budget, goal, what must keep running in an outage, roof
type) comes from here.

The five saved sample plans were set up by hand, with some numbers that do not match the city's, and every mismatch then
showed up as a "please confirm" item that a real visitor would never see. This module lets those samples be set up the same
way a visitor's are, so their reports hold only real questions. It reads the same free public datasets as the pre-fill, and
uses no Claude.
"""

from __future__ import annotations

import os
from typing import Any

from tools.city_energy import CityEnergyError, fetch_ll24, fetch_ll84
from tools.footprints import FootprintError, suggest_roof_area
from tools.geocode import GeocodeError, geocode_nyc_address
from tools.live_records import PLUTO_URL, LiveRecordsError
from tools.prefill import build_prefill
from tools.web import get_with_retry

TIMEOUT_SECONDS = 15


def _number(value: Any) -> float | None:
    """A number above zero from a text field, or None (the tax-lot file uses 0 and blanks for 'unknown')."""
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def fetch_tax_lot(bbl: str) -> dict[str, Any]:
    """The city's tax-lot record for one lot (floor area, year built, use, owner). Raises LiveRecordsError if there is none."""
    headers = {}
    token = os.environ.get("SODA_APP_TOKEN", "").strip()
    if token:
        headers["X-App-Token"] = token
    # The file's lot number is stored as a number ("4050430011.00000000"), so it is compared as one.
    response = get_with_retry(PLUTO_URL, params={"$where": f"bbl={int(bbl)}", "$limit": 1}, headers=headers, timeout=TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise LiveRecordsError(f"NYC Open Data error (HTTP {response.status_code}).")
    rows = response.json()
    if not rows:
        raise LiveRecordsError(f"NYC Open Data has no tax-lot record for lot {bbl}.")
    return rows[0]


def city_fields(address: str, borough: str) -> dict[str, Any]:
    """
    What the city's records fill in for this address, ready to merge into a building profile.

    Returns {"fields": {...}, "found": {...}, "missing": [...]}. `fields` holds only values the city actually has, using the
    same profile names the website's form sends to the planner. `found` says where the lot is, and `missing` lists, in plain
    words, anything the city had no record for (so the profile keeps whatever was already there for that part).
    """
    place = geocode_nyc_address(address, borough)
    bbl = str(place["bbl"])
    lot = fetch_tax_lot(bbl)

    try:
        ll84 = fetch_ll84(bbl)
    except CityEnergyError:
        ll84 = None
    try:
        ll24 = fetch_ll24(bbl)
    except CityEnergyError:
        ll24 = None
    try:
        roof = suggest_roof_area(address, borough)
    except (GeocodeError, FootprintError):
        roof = None

    prefill = build_prefill(bbl, ll84, ll24, roof)
    values = {item["field"]: item["value"] for item in prefill["items"]}

    fields: dict[str, Any] = {
        # The street exactly as the city writes it, so the lot's official street and the one entered always agree.
        "address": place["label"].split(",")[0].strip(),
        "borough": borough,
    }
    # The energy report's floor area when there is one (it matches the electricity figure); the tax lot's otherwise.
    floor_area = values.get("floor_area_sqft") or _number(lot.get("bldgarea"))
    if floor_area:
        fields["floor_area_sqft"] = int(round(floor_area))
    year = _number(lot.get("yearbuilt"))
    if year:
        fields["year_built"] = int(year)
    for name in ("annual_kwh", "roof_area_sqft", "existing_solar_kw"):
        if name in values:
            fields[name] = values[name]

    return {
        "fields": fields,
        "found": {"bbl": bbl, "label": place["label"], "owner": lot.get("ownername")},
        "missing": prefill["missing"],
    }
