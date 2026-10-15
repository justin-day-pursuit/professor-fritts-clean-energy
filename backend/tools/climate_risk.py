"""
Climate and hazard context tool (group 4).

v3 keeps this mock: the fixture stands in for FEMA and NYC flood maps and must
include heat, flood, and winter-storm ratings, flood zone, community resilience,
and data vintage. A live FEMA call is a later block.
"""

from __future__ import annotations

from mocks.mock_mode import require_mock_or_fixture
from tools.base import ToolResult


def get_hazard_context(case: str) -> ToolResult:
    """Return saved heat and flood exposure ratings for the building site."""
    return require_mock_or_fixture(case, "get_hazard_context")
