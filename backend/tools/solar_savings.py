"""
Solar production and storage optimization tools (group 2) — live PVWatts in v1, mock REopt.
"""

from __future__ import annotations

from typing import Any

from mocks.mock_mode import get_tool_mode, require_mock_or_fixture
from tools.base import ToolResult
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


def optimize_solar_storage(case: str) -> ToolResult:
    """Return saved REopt-style battery sizing for critical-load hours."""
    return require_mock_or_fixture(case, "optimize_solar_storage")
