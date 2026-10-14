"""
Live rooftop solar estimate — NYC geocoder plus PVWatts v8 (v1).

Used by get_solar_production when TOOL_MODE=live. Every call returns the exact PVWatts inputs
so a run can be repeated later and compared (build plan v1 goalpost: within ±1%).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

from tools.base import ToolResult
from tools.calculate import CalculateInput, run_calculate

GEOCODE_URL = "https://geosearch.planninglabs.nyc/v2/search"
PVWATTS_URL = "https://developer.nlr.gov/api/pvwatts/v8.json"
PVWATTS_DOCS_URL = "https://developer.nlr.gov/docs/solar/pvwatts/v8/"

TIMEOUT_SECONDS = 30

# Flat-roof defaults: fixed roof-mount array, low tilt, facing south, standard modules, 14% system losses.
PVWATTS_DEFAULTS: dict[str, Any] = {
    "module_type": 0,
    "losses": 14,
    "array_type": 1,
    "tilt": 10,
    "azimuth": 180,
}


class LiveSolarError(RuntimeError):
    """A live solar lookup failed in a way the agent should not paper over."""


def geocode_nyc_address(address: str, borough: str | None) -> dict[str, Any]:
    """Turn a street address into coordinates with the free NYC Planning Labs geocoder."""
    text = ", ".join(part for part in (address, borough, "NY") if part)
    response = httpx.get(GEOCODE_URL, params={"text": text, "size": 1}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        raise LiveSolarError(f"The NYC geocoder found no match for {text!r}.")
    props = features[0]["properties"]
    lon, lat = features[0]["geometry"]["coordinates"]
    street_number = address.split()[0]
    if not str(props.get("label", "")).startswith(street_number):
        raise LiveSolarError(f"Geocoder matched {props.get('label')!r}, which does not fit {address!r}.")
    return {
        "label": props.get("label"),
        "borough": props.get("borough"),
        "postalcode": props.get("postalcode"),
        "match_type": props.get("match_type"),
        "confidence": props.get("confidence"),
        "lat": lat,
        "lon": lon,
    }


def default_system_kw(profile: dict[str, Any]) -> float:
    """Size the array from roof area with the shared C1 and C2 formulas (setback 0.55, 66 sq ft per kW)."""
    roof = float(profile["roof_area_sqft"])
    usable = run_calculate(CalculateInput(formula="C1", inputs={"roof_area_sqft": roof})).data["value"]
    return float(run_calculate(CalculateInput(formula="C2", inputs={"usable_roof_sqft": usable})).data["value"])


def run_pvwatts(lat: float, lon: float, system_kw: float, api_key: str) -> dict[str, Any]:
    """Call PVWatts v8 and return its parsed JSON; raises LiveSolarError on API-reported errors."""
    params = {"api_key": api_key, "lat": lat, "lon": lon, "system_capacity": system_kw, **PVWATTS_DEFAULTS}
    response = httpx.get(PVWATTS_URL, params=params, timeout=TIMEOUT_SECONDS)
    payload = response.json()
    if response.status_code != 200 or payload.get("errors"):
        # Never echo the request URL: it carries the API key.
        raise LiveSolarError(f"PVWatts error (HTTP {response.status_code}): {payload.get('errors')}")
    return payload


def fetch_live_solar_production(profile: dict[str, Any], system_kw: float | None = None) -> ToolResult:
    """Estimate annual AC output for the building in the session profile using live data."""
    api_key = os.environ.get("NLR_API_KEY", "").strip()
    if not api_key:
        raise LiveSolarError("NLR_API_KEY is not set; add it to .env to use live solar data.")
    if not profile.get("address"):
        raise LiveSolarError("The intake profile has no address to look up.")

    place = geocode_nyc_address(profile["address"], profile.get("borough"))
    kw = float(system_kw) if system_kw else default_system_kw(profile)
    payload = run_pvwatts(place["lat"], place["lon"], kw, api_key)

    outputs = payload["outputs"]
    flags: list[str] = []
    if place["match_type"] != "exact":
        flags.append("address_match_approximate")

    return ToolResult(
        tool="get_solar_production",
        data={
            "system_kw_dc": kw,
            "annual_ac_kwh": outputs["ac_annual"],
            "capacity_factor": outputs["capacity_factor"] / 100,
            "solar_radiation_kwh_m2_day": outputs["solrad_annual"],
            "monthly_ac_kwh": outputs["ac_monthly"],
            "pvwatts_inputs": {"lat": place["lat"], "lon": place["lon"], "system_capacity": kw, **PVWATTS_DEFAULTS},
            "location": place,
            "weather_data_source": payload.get("station_info", {}).get("weather_data_source"),
        },
        source_url=PVWATTS_DOCS_URL,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version=f"pvwatts-v{payload.get('version', 'unknown')}",
        mock=False,
        flags=flags,
    )
