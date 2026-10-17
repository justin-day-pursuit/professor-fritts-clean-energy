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


# Fields of the intake's "existing systems" section: any one of them filled in counts as answering it.
EXISTING_SYSTEM_FIELDS: tuple[str, ...] = (
    "existing_renewables",
    "existing_efficiency",
    "existing_solar_kw",
)


# Optional intake fields that sharpen the plan. A blank one is listed under optional_missing (so the plan can say what
# it did not know) but it never blocks a run or adds a missing_field flag. "unknown" counts as blank.
OPTIONAL_PROFILE_FIELDS: tuple[str, ...] = (
    "owner_agency",
    "roof_condition",
    "lighting_type",
    "lighting_retrofit_year",
    "heating_fuel",
    "cooling_type",
    "has_building_controls",
    "goal_type",
    "goal_percent",
    "critical_load_kw",
    "backup_hours_wanted",
    "electricity_rate_usd_per_kwh",
)


def find_missing_optional_fields(profile: dict[str, Any]) -> list[str]:
    """Return the optional intake fields that are blank, in the order of OPTIONAL_PROFILE_FIELDS."""
    return [
        name
        for name in OPTIONAL_PROFILE_FIELDS
        if profile.get(name) is None
        or (isinstance(profile.get(name), str) and profile[name].strip().lower() in ("", "unknown"))
    ]


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
    # v6: the intake asks what renewable and efficiency systems the building already has. Writing "none" or
    # a 0 is an answer; leaving the whole section blank is not, so the plan asks once instead of assuming.
    if not any(_answered(profile, key) for key in EXISTING_SYSTEM_FIELDS):
        missing.append("existing_systems")
    return missing


def _answered(profile: dict[str, Any], key: str) -> bool:
    """True when the intake field has any answer at all, including "none" and a number 0."""
    value = profile.get(key)
    if value is None:
        return False
    return not (isinstance(value, str) and value.strip() == "")


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
        data={
            "profile": session_profile,
            "missing_fields": missing,
            "optional_missing": find_missing_optional_fields(session_profile),
        },
        source_url="session://profile",
        retrieved_at="",
        dataset_version="session-v0",
        mock=False,
        flags=[f"missing_field:{name}" for name in missing] + list(session_profile.get("profile_flags") or []),
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
