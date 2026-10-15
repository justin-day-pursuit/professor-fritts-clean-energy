"""
Utility rates and NY incentives search tools (group 3) — live EIA price in v1, mock program lists.
"""

from __future__ import annotations

from typing import Any

from mocks.mock_mode import get_tool_mode, require_mock_or_fixture
from tools.base import ToolResult
from tools.live_rates import fetch_live_utility_rates


def get_utility_rates(case: str, profile: dict[str, Any] | None = None) -> ToolResult:
    """Return the live EIA price in live mode, or the saved tariff in mock mode."""
    if get_tool_mode() == "live":
        return fetch_live_utility_rates(profile or {})
    return require_mock_or_fixture(case, "get_utility_rates")


def search_ny_incentives_and_rules(case: str) -> ToolResult:
    """Return saved incentive and rule snippets with status and retrieval dates."""
    return require_mock_or_fixture(case, "search_ny_incentives_and_rules")
