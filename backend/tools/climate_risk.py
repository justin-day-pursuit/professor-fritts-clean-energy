"""
Climate and hazard context tool (group 4) — mock FEMA-style ratings in v0.
"""

from __future__ import annotations

from mocks.mock_mode import require_mock_or_fixture
from tools.base import ToolResult


def get_hazard_context(case: str) -> ToolResult:
    """Return saved heat and flood exposure ratings for the building site."""
    return require_mock_or_fixture(case, "get_hazard_context")
