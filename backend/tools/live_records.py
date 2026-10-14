"""
Live New York City building records from NYC Open Data's PLUTO tax-lot dataset (v1).

Used by lookup_ny_building_records when TOOL_MODE=live. The tool reports what the city says and
lists where that disagrees with the intake; it never overwrites what the user typed.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from tools.base import ToolResult
from tools.geocode import geocode_nyc_address, is_approximate
from tools.web import get_with_retry

PLUTO_URL = "https://data.cityofnewyork.us/resource/64uk-42ks.json"
PLUTO_SOURCE_URL = "https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks"

TIMEOUT_SECONDS = 30
AREA_MISMATCH_RATIO = 0.10  # flag floor areas that differ by more than 10%


class LiveRecordsError(RuntimeError):
    """A live building-records lookup failed in a way the agent should not paper over."""


def _number(value: Any) -> float | None:
    """PLUTO sends every number as text; blank or missing becomes None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
    if not profile.get("borough"):
        raise LiveRecordsError("The intake profile has no borough; ask which borough the building is in.")

    place = geocode_nyc_address(address, profile["borough"])
    if not place.get("bbl"):
        raise LiveRecordsError(f"The geocoder returned no tax lot (BBL) for {place['label']!r}.")

    headers = {}
    if os.environ.get("SODA_APP_TOKEN", "").strip():
        headers["X-App-Token"] = os.environ["SODA_APP_TOKEN"].strip()
    response = get_with_retry(
        PLUTO_URL,
        params={"$where": f"bbl='{place['bbl']}.00000000'", "$limit": 1},
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
    city_year = int(_number(row.get("yearbuilt")) or 0) or None  # PLUTO uses 0 for "unknown"
    differences = _compare_with_intake(profile, city_area, city_year)

    flags = [f"intake_mismatch:{d['field']}" for d in differences]
    if is_approximate(place):
        flags.append("address_match_approximate")

    return ToolResult(
        tool="lookup_ny_building_records",
        data={
            "address": row.get("address"),
            "borough": profile["borough"],
            "bbl": place["bbl"],
            "zipcode": row.get("zipcode"),
            "gross_floor_area_sqft": city_area,
            "lot_area_sqft": _number(row.get("lotarea")),
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
