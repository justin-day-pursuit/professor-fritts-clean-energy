"""
Building profile and New York public-records tools (group 1).

get_building_profile reads the live session intake; lookup_ny_building_records uses live PLUTO
records in live mode and mock fixtures otherwise.
"""

from __future__ import annotations

from typing import Any

from mocks.mock_mode import get_tool_mode, require_mock_or_fixture
from tools.base import ToolResult
from tools.live_records import fetch_live_building_records


# Intake fields the plan needs. If one is blank, the tool flags it so the agent states an
# assumption (or asks) instead of quietly inventing a value. Add a field here to start tracking it.
REQUIRED_PROFILE_FIELDS: tuple[str, ...] = (
    "address",
    "borough",
    "building_type",
    "floor_area_sqft",
    "year_built",
    "roof_type",
    "roof_area_sqft",
    "roof_replaced_year",
    "utility",
    "annual_kwh",
    "budget_amount",
    "budget_year",
    "budget_type",
    "goal",
    "target_year",
    "critical_loads",
)


def find_missing_profile_fields(profile: dict[str, Any]) -> list[str]:
    """
    Return the required intake fields that are empty, in the order of REQUIRED_PROFILE_FIELDS.

    None, blank text and the word 'unknown' count as missing; a real 0 does not (a roof
    replaced in year 0 is nonsense, but a budget of 0 is a clear answer the user gave).
    """
    missing = []
    for name in REQUIRED_PROFILE_FIELDS:
        value = profile.get(name)
        if value is None or (isinstance(value, str) and value.strip().lower() in ("", "unknown")):
            missing.append(name)
    return missing


def get_building_profile(session_profile: dict[str, Any]) -> ToolResult:
    """
    Return the intake profile already stored on the session — no external API.

    The harness passes session.profile here so the agent sees the same fields the user typed.
    From v2 the result also lists missing fields (data.missing_fields) and adds one
    'missing_field:<name>' flag per gap so the roadmap can say what is unknown.
    """
    missing = find_missing_profile_fields(session_profile)
    return ToolResult(
        tool="get_building_profile",
        data={"profile": session_profile, "missing_fields": missing},
        source_url="session://profile",
        retrieved_at="",
        dataset_version="session-v0",
        mock=False,
        flags=[f"missing_field:{name}" for name in missing],
    )


def lookup_ny_building_records(
    case: str,
    address: str | None = None,
    profile: dict[str, Any] | None = None,
) -> ToolResult:
    """Return live PLUTO records in live mode, or fictional records from the case fixture folder."""
    if get_tool_mode() == "live":
        return fetch_live_building_records(profile or {}, address)
    result = require_mock_or_fixture(case, "lookup_ny_building_records")
    if address:
        result.data.setdefault("query", {})["address"] = address
    return result
