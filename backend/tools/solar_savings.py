"""
Solar production and storage optimization tools (group 2) — live PVWatts in v1, mock REopt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mocks.mock_mode import get_tool_mode, require_mock_or_fixture
from tools.base import ToolResult, ToolUnavailableError
from tools.live_solar import fetch_live_solar_production
from tools.roof import (
    check_new_array_fits,
    check_roof_sizing_allowed,
    existing_solar_kw,
    free_array_kw,
    roof_kind,
)


def get_solar_production(
    case: str,
    profile: dict[str, Any] | None = None,
    system_kw: float | None = None,
) -> ToolResult:
    """
    Return live PVWatts output in live mode, or the saved fixture in mock mode.

    v6 rules apply in both modes. A roof that is not flat is not sized from the flat-roof defaults until an
    engineer or roofer has verified its usable area. An array that does not fit beside the solar already on
    the roof is refused. A result for a roof that is not flat carries the flag pitched_roof_output_not_modeled,
    because the PVWatts tilt and direction are the flat-roof defaults, not the real roof's.
    """
    profile = profile or {}
    check_roof_sizing_allowed(profile)
    check_new_array_fits(profile, system_kw)
    if system_kw is None and existing_solar_kw(profile) > 0:
        # Without an explicit size the live tool sizes the array itself, using only the free roof.
        system_kw = free_array_kw(profile)
    if get_tool_mode() == "live":
        result = fetch_live_solar_production(profile, system_kw)
    else:
        result = require_mock_or_fixture(case, "get_solar_production")
    flags = list(result.flags)
    if roof_kind(profile.get("roof_type")) == "non_flat" and "pitched_roof_output_not_modeled" not in flags:
        flags.append("pitched_roof_output_not_modeled")
    data = dict(result.data)
    if existing_solar_kw(profile) > 0:
        data["existing_solar_kw"] = existing_solar_kw(profile)
        data["free_capacity_kw"] = round(free_array_kw(profile) or 0.0, 1)
    return result.model_copy(update={"flags": flags, "data": data})


# Battery sizing: round-trip efficiency, the default backup length, and the stand-in critical load when the user gave none.
BATTERY_EFFICIENCY = 0.85
DEFAULT_BACKUP_HOURS = 8.0
ESTIMATED_CRITICAL_WATTS_PER_SQFT = 1.0


def _number(value: Any) -> float | None:
    """A positive number from an intake value, or None when blank or not usable."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def size_battery_from_profile(profile: dict[str, Any]) -> ToolResult:
    """
    Size a backup battery from the user's own numbers: kW = critical load, kWh = kW x hours / 0.85.

    Real inputs come first. When the user left the critical load blank it is estimated from floor area
    (about 1 W per sq ft), and blank backup hours default to 8; each estimate is named in the assumption
    text and in a flag so the plan labels it an ASSUMPTION. With neither a critical load nor a floor area
    there is nothing to size from, so the tool reports itself unavailable instead of inventing a number.
    """
    kw = _number(profile.get("critical_load_kw"))
    hours = _number(profile.get("backup_hours_wanted"))
    flags: list[str] = []
    parts: list[str] = []
    if kw is None:
        floor_area = _number(profile.get("floor_area_sqft"))
        if floor_area is None:
            raise ToolUnavailableError(
                "Battery sizing needs a critical load in kW or a floor area; the intake has neither."
            )
        kw = round(floor_area * ESTIMATED_CRITICAL_WATTS_PER_SQFT / 1000.0, 1)
        flags.append("battery_inputs_estimated")
        parts.append(
            f"Critical load not given, so estimated at {ESTIMATED_CRITICAL_WATTS_PER_SQFT} W per sq ft x "
            f"{floor_area:g} sq ft = {kw} kW (a team placeholder, not metered)."
        )
    else:
        parts.append(f"Critical load of {kw:g} kW as entered by the user.")
    if hours is None:
        hours = DEFAULT_BACKUP_HOURS
        if "battery_inputs_estimated" not in flags:
            flags.append("battery_inputs_estimated")
        parts.append(f"Backup length not given, so {DEFAULT_BACKUP_HOURS:g} hours assumed.")
    else:
        parts.append(f"Backup length of {hours:g} hours as entered by the user.")
    kwh = round(kw * hours / BATTERY_EFFICIENCY)
    parts.append(f"Battery energy = kW x hours / {BATTERY_EFFICIENCY} round-trip efficiency = {kwh} kWh.")
    return ToolResult(
        tool="optimize_solar_storage",
        data={
            "battery_kw": kw,
            "battery_kwh": kwh,
            "critical_load_kw": kw,
            "critical_load_hours": hours,
            "notes": " ".join(parts),
        },
        source_url="internal://optimize_solar_storage",
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version="battery-sizing-v1",
        mock=False,
        flags=flags,
    )


def optimize_solar_storage(case: str, profile: dict[str, Any] | None = None) -> ToolResult:
    """
    Size the backup battery. Live mode sizes from the user's intake; mock mode returns the saved sample
    so recorded and scripted demos replay unchanged.
    """
    if get_tool_mode() == "live":
        return size_battery_from_profile(profile or {})
    return require_mock_or_fixture(case, "optimize_solar_storage")
