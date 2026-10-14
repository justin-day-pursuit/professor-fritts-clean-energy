"""
Utility rates and NY incentives search tools (group 3) — mock OpenEI and program lists in v0.
"""

from __future__ import annotations

from mocks.mock_mode import require_mock_or_fixture
from tools.base import ToolResult


def get_utility_rates(case: str) -> ToolResult:
    """Return saved commercial tariff data for the eval case."""
    return require_mock_or_fixture(case, "get_utility_rates")


def search_ny_incentives_and_rules(case: str) -> ToolResult:
    """Return saved incentive and rule snippets with status and retrieval dates."""
    return require_mock_or_fixture(case, "search_ny_incentives_and_rules")
