"""
Building profile and New York public-records tools (group 1).

get_building_profile reads the live session intake; lookup_ny_building_records uses mock fixtures in v0.
"""

from __future__ import annotations

from typing import Any

from mocks.mock_mode import require_mock_or_fixture
from tools.base import ToolResult


def get_building_profile(session_profile: dict[str, Any]) -> ToolResult:
    """
    Return the intake profile already stored on the session — no external API.

    The harness passes session.profile here so the agent sees the same fields the user typed.
    """
    return ToolResult(
        tool="get_building_profile",
        data={"profile": session_profile},
        source_url="session://profile",
        retrieved_at="",
        dataset_version="session-v0",
        mock=False,
    )


def lookup_ny_building_records(case: str, address: str | None = None) -> ToolResult:
    """Load fictional NYC Open Data-style records from the case fixture folder."""
    result = require_mock_or_fixture(case, "lookup_ny_building_records")
    if address:
        result.data.setdefault("query", {})["address"] = address
    return result
