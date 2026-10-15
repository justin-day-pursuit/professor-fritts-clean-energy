"""
Live rooftop solar estimate — NYC geocoder plus PVWatts v8 (v1).

Used by get_solar_production when TOOL_MODE=live. Every call returns the exact PVWatts inputs
so a run can be repeated later and compared (build plan v1 goalpost: within ±1%).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from tools.base import ToolResult
from tools.calculate import CalculateInput, run_calculate
from tools.geocode import borough_of, geocode_nyc_address, is_approximate
from tools.web import get_with_retry

PVWATTS_URL = "https://developer.nlr.gov/api/pvwatts/v8.json"
PVWATTS_DOCS_URL = "https://developer.nlr.gov/docs/solar/pvwatts/v8/"

TIMEOUT_SECONDS = 20

# Flat-roof defaults: fixed roof-mount array, low tilt, facing south, standard modules, 14% system losses.
PVWATTS_DEFAULTS: dict[str, Any] = {
    "module_type": 0,
    "losses": 14,
    "array_type": 1,
    "tilt": 10,
    "azimuth": 180,
}

# The kWh range reruns PVWatts at lower and higher system losses (soiling, wiring, inverter, shading).
# These two values are our assumption, not PVWatts output; the result says so in range_assumption.
LOSSES_LOW_OUTPUT = 18
LOSSES_HIGH_OUTPUT = 10


class LiveSolarError(RuntimeError):
    """A live solar lookup failed in a way the agent should not paper over."""


def default_system_kw(profile: dict[str, Any]) -> float:
    """Size the array from roof area with the shared C1 and C2 formulas (setback 0.55, 66 sq ft per kW)."""
    try:
        roof = float(profile.get("roof_area_sqft"))
    except (TypeError, ValueError):
        roof = 0.0
    if roof <= 0:
        raise LiveSolarError("The intake profile has no valid roof area to size the solar array.")
    usable = run_calculate(CalculateInput(formula="C1", inputs={"roof_area_sqft": roof})).data["value"]
    return float(run_calculate(CalculateInput(formula="C2", inputs={"usable_roof_sqft": usable})).data["value"])


def rerun_pvwatts(inputs: dict[str, Any], api_key: str) -> dict[str, Any]:
    """Call PVWatts v8 with a full set of inputs (as logged in a result's pvwatts_inputs); raises LiveSolarError on API errors."""
    response = get_with_retry(PVWATTS_URL, params={"api_key": api_key, **inputs}, timeout=TIMEOUT_SECONDS)
    payload = response.json()
    if response.status_code != 200 or payload.get("errors"):
        # Never echo the request URL: it carries the API key.
        raise LiveSolarError(f"PVWatts error (HTTP {response.status_code}): {payload.get('errors')}")
    return payload


def run_pvwatts(lat: float, lon: float, system_kw: float, api_key: str) -> dict[str, Any]:
    """Call PVWatts v8 for one site with the flat-roof defaults."""
    inputs = {"lat": lat, "lon": lon, "system_capacity": system_kw, **PVWATTS_DEFAULTS}
    return rerun_pvwatts(inputs, api_key)


def fetch_live_solar_production(profile: dict[str, Any], system_kw: float | None = None) -> ToolResult:
    """Estimate annual AC output for the building in the session profile using live data."""
    api_key = os.environ.get("NLR_API_KEY", "").strip()
    if not api_key:
        raise LiveSolarError("NLR_API_KEY is not set; add it to .env to use live solar data.")
    if not profile.get("address"):
        raise LiveSolarError("The intake profile has no address to look up.")
    borough = borough_of(profile)
    if not borough:
        # Without it the geocoder can match a same-named street in another borough.
        raise LiveSolarError("The intake profile has no borough; ask which borough the building is in.")
    # Size the array first so bad intake values fail before any web call is made.
    kw = float(system_kw) if system_kw else default_system_kw(profile)

    place = geocode_nyc_address(profile["address"], borough)
    payload = run_pvwatts(place["lat"], place["lon"], kw, api_key)
    base_inputs = {"lat": place["lat"], "lon": place["lon"], "system_capacity": kw, **PVWATTS_DEFAULTS}
    # Two extra PVWatts calls with the same inputs but different losses give the low and high end of the kWh range.
    low = rerun_pvwatts({**base_inputs, "losses": LOSSES_LOW_OUTPUT}, api_key)["outputs"]["ac_annual"]
    high = rerun_pvwatts({**base_inputs, "losses": LOSSES_HIGH_OUTPUT}, api_key)["outputs"]["ac_annual"]

    outputs = payload["outputs"]
    flags: list[str] = []
    if is_approximate(place):
        flags.append("address_match_approximate")

    return ToolResult(
        tool="get_solar_production",
        data={
            "system_kw_dc": kw,
            "annual_ac_kwh": outputs["ac_annual"],
            "annual_ac_kwh_low": low,
            "annual_ac_kwh_high": high,
            "range_assumption": (
                f"ASSUMPTION: system losses of {LOSSES_LOW_OUTPUT}% (low) to {LOSSES_HIGH_OUTPUT}% (high) "
                f"around PVWatts' {PVWATTS_DEFAULTS['losses']}% default; weather is typical-year data."
            ),
            "capacity_factor": outputs["capacity_factor"] / 100,
            "solar_radiation_kwh_m2_day": outputs["solrad_annual"],
            "monthly_ac_kwh": outputs["ac_monthly"],
            "pvwatts_inputs": base_inputs,
            "location": place,
            "weather_data_source": payload.get("station_info", {}).get("weather_data_source"),
        },
        source_url=PVWATTS_DOCS_URL,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version=f"pvwatts-v{payload.get('version', 'unknown')}",
        mock=False,
        flags=flags,
    )
