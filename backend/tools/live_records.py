"""
Live New York City building records from NYC Open Data's PLUTO tax-lot dataset (v1).

Used by lookup_ny_building_records when TOOL_MODE=live. The tool reports what the city says and
lists where that disagrees with the intake; it never overwrites what the user typed.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

from tools.base import ToolResult
from tools.geocode import borough_of, geocode_nyc_address, is_approximate
from tools.web import get_with_retry

PLUTO_URL = "https://data.cityofnewyork.us/resource/64uk-42ks.json"
PLUTO_SOURCE_URL = "https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks"

TIMEOUT_SECONDS = 15
AREA_MISMATCH_RATIO = 0.10  # flag floor areas that differ by more than 10%


class LiveRecordsError(RuntimeError):
    """A live building-records lookup failed in a way the agent should not paper over."""


def _number(value: Any) -> float | None:
    """PLUTO sends every number as text; blank or missing becomes None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _street_name(address: str | None) -> str:
    """
    Street words after the house number, with short suffixes spelled out.

    "41-17 Main Street" and "41-24 Kissena Boulevard" can then be compared even when
    one of them is another frontage of the same tax lot.
    """
    if not address:
        return ""
    suffix = {
        "ST": "STREET",
        "AVE": "AVENUE",
        "BLVD": "BOULEVARD",
        "RD": "ROAD",
        "DR": "DRIVE",
        "PL": "PLACE",
        "LN": "LANE",
        "CT": "COURT",
        "PKWY": "PARKWAY",
        "TER": "TERRACE",
    }
    stop = {"NY", "USA", "NEW", "YORK", "FLUSHING", "QUEENS", "BROOKLYN", "MANHATTAN", "BRONX", "STATEN", "ISLAND"}
    parts = re.sub(r"[^A-Za-z0-9\- ]", " ", address).upper().split()
    if parts and any(ch.isdigit() for ch in parts[0]):
        parts = parts[1:]
    # A street suffix ends the street name. Looking for it first keeps streets that start with a place
    # word ("Queens Boulevard", "New York Avenue") intact. Index 0 is skipped so "St Marks Place" is not cut at "St".
    for index, part in enumerate(parts):
        if index >= 1 and (part in suffix or part in set(suffix.values())):
            return " ".join(parts[:index] + [suffix.get(part, part)])
    # No suffix ("41-17 Main, Queens"): the street runs until the first place name after at least one street word.
    name: list[str] = []
    for part in parts:
        if part in stop and name:
            break
        name.append(part)
    return " ".join(name)


def _lot_matches_intake_floor(profile: dict[str, Any], lot_area: float | None) -> bool:
    """True when the land area is within 10% of the floor area the user typed."""
    intake_area = _number(profile.get("floor_area_sqft"))
    if not intake_area or not lot_area:
        return False
    return abs(lot_area - intake_area) / intake_area <= AREA_MISMATCH_RATIO


def _compare_with_intake(profile: dict[str, Any], city_area: float | None, city_year: int | None) -> list[dict[str, Any]]:
    """List the fields where the city record and the intake disagree."""
    differences = []
    intake_area = _number(profile.get("floor_area_sqft"))
    if intake_area and city_area and abs(city_area - intake_area) / intake_area > AREA_MISMATCH_RATIO:
        differences.append({"field": "floor_area_sqft", "intake": intake_area, "city_record": city_area})
    intake_year = _number(profile.get("year_built"))
    if intake_year and city_year and int(intake_year) != city_year:
        differences.append({"field": "year_built", "intake": int(intake_year), "city_record": city_year})
    return differences


def fetch_live_building_records(profile: dict[str, Any], address: str | None = None) -> ToolResult:
    """Look up the tax lot for the building's address and return its city records."""
    address = address or profile.get("address")
    if not address:
        raise LiveRecordsError("No address to look up.")
    borough = borough_of(profile)
    if not borough:
        raise LiveRecordsError("The intake profile has no borough; ask which borough the building is in.")

    place = geocode_nyc_address(address, borough)
    if not str(place.get("bbl") or "").isdigit():
        raise LiveRecordsError(f"The geocoder returned no tax lot (BBL) for {place['label']!r}.")

    headers = {}
    if os.environ.get("SODA_APP_TOKEN", "").strip():
        headers["X-App-Token"] = os.environ["SODA_APP_TOKEN"].strip()
    # PLUTO's bbl column is a number (it prints as "4050430011.00000000"), so compare it as a number.
    response = get_with_retry(
        PLUTO_URL,
        params={"$where": f"bbl={int(place['bbl'])}", "$limit": 1},
        headers=headers,
        timeout=TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise LiveRecordsError(f"NYC Open Data error (HTTP {response.status_code}).")
    rows = response.json()
    if not rows:
        raise LiveRecordsError(f"NYC Open Data has no PLUTO record for lot {place['bbl']}.")
    row = rows[0]

    city_area = _number(row.get("bldgarea"))
    lot_area = _number(row.get("lotarea"))
    city_year = int(_number(row.get("yearbuilt")) or 0) or None  # PLUTO uses 0 for "unknown"
    differences = _compare_with_intake(profile, city_area, city_year)

    flags = [f"intake_mismatch:{d['field']}" for d in differences]
    if is_approximate(place):
        flags.append("address_match_approximate")
    # Confidence 0.8 can still point at a lot whose official street is not the one we asked for.
    asked_street = _street_name(address)
    recorded_street = _street_name(str(row.get("address") or ""))
    if asked_street and recorded_street and asked_street != recorded_street:
        flags.append("address_street_mismatch")

    return ToolResult(
        tool="lookup_ny_building_records",
        data={
            "address": row.get("address"),
            "borough": borough,
            "bbl": place["bbl"],
            "zipcode": row.get("zipcode"),
            "gross_floor_area_sqft": city_area,
            "lot_area_sqft": lot_area,
            "lot_matches_intake_floor": _lot_matches_intake_floor(profile, lot_area),
            "num_floors": _number(row.get("numfloors")),
            "year_built": city_year,
            "building_class": row.get("bldgclass"),
            "land_use_code": row.get("landuse"),
            "landmark_flag": bool(row.get("landmark")) or bool(row.get("histdist")),
            "differs_from_intake": differences,
            "geocoder_match": place["label"],
        },
        source_url=PLUTO_SOURCE_URL,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version=f"pluto-{row.get('version', 'unknown')}",
        mock=False,
        flags=flags,
    )
