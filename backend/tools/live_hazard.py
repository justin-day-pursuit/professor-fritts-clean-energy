"""
Live flood-zone lookup from FEMA's National Flood Hazard Layer (v7).

Used by get_hazard_context when TOOL_MODE=live. It asks FEMA's public map service which flood zone covers the
building's address point. Only the CURRENT effective map is read (Hurricane Sandy's old surge line is not used).

What it does not do, and says so in its notes: it does not check the 2015 preliminary map that NYC code also
considers, and it does not look up heat or winter-storm ratings. Nothing is guessed to fill those gaps.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from tools.base import ToolResult, ToolUnavailableError
from tools.geocode import GeocodeError, borough_of, geocode_nyc_address
from tools.web import get_with_retry

NFHL_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
NFHL_SOURCE_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28"
TIMEOUT_SECONDS = 25

# Zones that FEMA calls a Special Flood Hazard Area (1%-annual-chance): the insurance and construction rules apply.
HIGH_RISK_PREFIXES = ("A", "V")


def parse_flood_features(features: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Reduce FEMA's answer for one point to a zone, its subtype and whether it is a high-risk area.

    More than one polygon can cover a point; the highest-risk one wins (a V or A zone beats a shaded X).
    No polygon means FEMA has no mapped zone there, which is reported as such, not as zone X.
    """
    zones = [f.get("attributes") or {} for f in features]
    zones = [z for z in zones if z.get("FLD_ZONE")]
    if not zones:
        return {"flood_zone": None, "zone_subtype": None, "special_flood_hazard_area": None}
    zones.sort(key=lambda z: (not str(z["FLD_ZONE"]).upper().startswith(HIGH_RISK_PREFIXES), str(z["FLD_ZONE"])))
    best = zones[0]
    zone = str(best["FLD_ZONE"]).upper()
    return {
        "flood_zone": zone,
        "zone_subtype": best.get("ZONE_SUBTY"),
        "special_flood_hazard_area": zone.startswith(HIGH_RISK_PREFIXES),
    }


def fetch_live_hazard(profile: dict[str, Any]) -> ToolResult:
    """Find the FEMA flood zone at the building's address. Raises ToolUnavailableError when it cannot."""
    address = profile.get("address")
    if not address:
        raise ToolUnavailableError("No address to look up a flood zone for.")
    try:
        place = geocode_nyc_address(address, borough_of(profile))
    except (GeocodeError, httpx.HTTPError) as exc:
        raise ToolUnavailableError(f"Could not place the address on the map: {exc}") from exc
    params = {
        "geometry": f"{place['lon']},{place['lat']}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
        "returnGeometry": "false",
        "f": "json",
    }
    try:
        response = get_with_retry(NFHL_URL, params=params, timeout=TIMEOUT_SECONDS)
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ToolUnavailableError(f"FEMA flood map request failed: {exc}") from exc
    if response.status_code != 200 or "features" not in body:
        raise ToolUnavailableError("FEMA flood map returned no usable answer.")
    zone = parse_flood_features(body["features"])
    notes = (
        "FEMA effective flood map (current), read at the address point. NYC code uses the more restrictive of the "
        "effective and 2015 preliminary maps; the preliminary map was not checked. Heat and winter-storm ratings "
        "were not looked up."
    )
    if zone["flood_zone"] is None:
        notes = "FEMA has no mapped flood zone at this point. " + notes
    flags = ["hazard_partial"]
    if is_approximate_place(place):
        flags.append("address_match_approximate")
    return ToolResult(
        tool="get_hazard_context",
        data={**zone, "notes": notes, "geocoder_match": place["label"]},
        source_url=NFHL_SOURCE_URL,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version="fema-nfhl-effective",
        mock=False,
        flags=flags,
    )


def is_approximate_place(place: dict[str, Any]) -> bool:
    """True when the geocoder was not confident, so the point may not be the building's own."""
    from tools.geocode import is_approximate

    return is_approximate(place)
