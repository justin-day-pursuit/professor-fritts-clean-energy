"""
Climate and hazard context tool (group 4).

Live mode reads the FEMA flood zone for the address (tools/live_hazard.py); heat and storm ratings are not
looked up and the result says so. Mock mode returns the saved fixture, which stands in for FEMA and NYC flood
maps and includes heat, flood and winter-storm ratings, flood zone, community resilience and data vintage.
"""

from __future__ import annotations

from typing import Any

from mocks.mock_mode import get_tool_mode, require_mock_or_fixture
from tools.base import ToolResult
from tools.live_hazard import fetch_live_hazard


def get_hazard_context(case: str, profile: dict[str, Any] | None = None) -> ToolResult:
    """Live: the FEMA flood zone at the address. Mock: saved heat and flood exposure ratings for the site."""
    if get_tool_mode() == "live":
        return fetch_live_hazard(profile or {})
    return require_mock_or_fixture(case, "get_hazard_context")
