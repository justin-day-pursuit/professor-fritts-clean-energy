"""
Roof-area suggestion from the city's building footprints (v6).

The planner cannot size solar without a roof area, and the intake form makes the user type one.
Many users do not know it. NYC Open Data publishes the outline (footprint) of every building, so
this module finds the outlines on a building's tax lot and adds up their ground area. That number
is only a SUGGESTION: a footprint is the ground area under a building, not a measured, usable roof.
It does not know about pitched roofs, towers, mechanical equipment or setbacks, and a lot can hold
several buildings. The form shows it with its source and asks the user to confirm it, and the plan
tells the user to have an engineer or roofer verify the usable area before anything is designed.

Why the area is computed from the outline and not read from the dataset's `shape_area` column: that
column is neither square feet nor square meters (it came out at a constant 1/6.15 of the true area
when checked against the outlines on Oct 15, 2026), so it is ignored here.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from typing import Any

from tools.geocode import geocode_nyc_address
from tools.web import get_with_retry

FOOTPRINTS_URL = "https://data.cityofnewyork.us/resource/5zhs-2jue.json"
FOOTPRINTS_SOURCE_URL = "https://data.cityofnewyork.us/City-Government/Building-Footprints/5zhs-2jue"
TIMEOUT_SECONDS = 20

# Feet in one degree of latitude. Longitude shrinks by cos(latitude), applied per outline below.
FEET_PER_DEGREE = 364_567.2

# Structures smaller than this (sheds, vents, entrance canopies) are listed but not added to the total.
MIN_BUILDING_SQFT = 200.0


class FootprintError(RuntimeError):
    """The footprint lookup failed; the roof area has to come from the user."""


def _ring_area_sqft(ring: list[list[float]]) -> float:
    """
    Ground area in square feet of one closed ring of [longitude, latitude] points.

    The points are flattened onto a plane around the ring's own latitude and measured with the
    shoelace formula. At the size of a building this is accurate to well under 1%.
    """
    if len(ring) < 3:
        return 0.0
    lat0 = sum(point[1] for point in ring) / len(ring)
    kx = math.cos(math.radians(lat0)) * FEET_PER_DEGREE
    pts = [(lon * kx, lat * FEET_PER_DEGREE) for lon, lat, *_ in ring]
    total = 0.0
    for i, (x1, y1) in enumerate(pts):
        x2, y2 = pts[(i + 1) % len(pts)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def polygon_area_sqft(geometry: dict[str, Any]) -> float:
    """
    Area in square feet of a GeoJSON Polygon or MultiPolygon, with holes (courtyards) taken out.

    Anything else, or a missing geometry, counts as zero.
    """
    kind = (geometry or {}).get("type")
    coords = (geometry or {}).get("coordinates") or []
    if kind == "Polygon":
        polygons = [coords]
    elif kind == "MultiPolygon":
        polygons = coords
    else:
        return 0.0
    area = 0.0
    for rings in polygons:
        if not rings:
            continue
        area += _ring_area_sqft(rings[0]) - sum(_ring_area_sqft(hole) for hole in rings[1:])
    return max(area, 0.0)


def _number(value: Any) -> float | None:
    """The dataset sends numbers as text; blank or missing becomes None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_footprints(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Turn the raw footprint rows for one lot into the building list and the suggested roof area.

    Only rows marked "Constructed" count (planned or demolished outlines are skipped). Each building
    keeps its ground area, roof height and year so a person can see what was added up.
    """
    buildings: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("last_status_type") or "Constructed").lower() != "constructed":
            continue
        area = polygon_area_sqft(row.get("the_geom") or {})
        if area <= 0:
            continue
        buildings.append(
            {
                "area_sqft": round(area),
                "height_ft": _number(row.get("height_roof")),
                "construction_year": int(_number(row.get("construction_year")) or 0) or None,
                "name": row.get("name") or None,
                "counted": area >= MIN_BUILDING_SQFT,
            }
        )
    buildings.sort(key=lambda b: b["area_sqft"], reverse=True)
    counted = [b for b in buildings if b["counted"]]
    total = sum(b["area_sqft"] for b in counted)
    return {
        "buildings": buildings,
        "building_count": len(counted),
        "total_footprint_sqft": total,
        "largest_footprint_sqft": counted[0]["area_sqft"] if counted else 0,
        # Rounded to the nearest 10 so the form does not suggest false precision.
        "suggested_roof_area_sqft": int(round(total, -1)),
    }


def fetch_footprints(bbl: str | int) -> dict[str, Any]:
    """Download and add up the building outlines on one tax lot (BBL); raises FootprintError on failure."""
    headers = {}
    if os.environ.get("SODA_APP_TOKEN", "").strip():
        headers["X-App-Token"] = os.environ["SODA_APP_TOKEN"].strip()
    response = get_with_retry(
        FOOTPRINTS_URL,
        params={
            "$select": "base_bbl,height_roof,construction_year,last_status_type,name,the_geom",
            "$where": f"base_bbl='{int(bbl)}'",
            "$limit": 50,
        },
        headers=headers,
        timeout=TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise FootprintError(f"NYC Open Data footprints error (HTTP {response.status_code}).")
    summary = summarize_footprints(response.json())
    if not summary["building_count"]:
        raise FootprintError(f"No building footprints found on lot {bbl}.")
    return summary


def suggest_roof_area(address: str, borough: str | None) -> dict[str, Any]:
    """
    Find the lot for an address and return the suggested roof area with its source.

    The note is written for the person filling in the form. Raises GeocodeError or FootprintError
    when the lot or its outlines cannot be found, so the caller can say the user must type the area.
    """
    place = geocode_nyc_address(address, borough)
    if not str(place.get("bbl") or "").isdigit():
        raise FootprintError(f"The geocoder returned no tax lot (BBL) for {place['label']!r}.")
    summary = fetch_footprints(place["bbl"])
    count = summary["building_count"]
    return {
        **summary,
        "bbl": place["bbl"],
        "geocoder_match": place["label"],
        "source_url": FOOTPRINTS_SOURCE_URL,
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            f"Ground area of {count} building outline{'s' if count != 1 else ''} on this tax lot, from NYC "
            "building footprints. It is not a measured roof: pitched roofs, towers, equipment and setbacks "
            "are not accounted for, and the lot may hold buildings that are not yours. Confirm the roof area "
            "with an engineer or roofer before design."
        ),
    }
