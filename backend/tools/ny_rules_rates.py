"""
Utility rates, tariff and NY incentives search tools (group 3) — live EIA price in v1, mock program lists.
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
    """Return saved incentive and rule snippets with status and retrieval dates (v4: conflict detection)."""
    result = require_mock_or_fixture(case, "search_ny_incentives_and_rules")
    flags = list(result.flags)
    for program in result.data.get("programs", []):
        if program.get("conflict") and "cached_live_conflict" not in flags:
            flags.append("cached_live_conflict")
    return result.model_copy(update={"flags": flags})


def get_utility_tariff(case: str) -> ToolResult:
    """
    Return the named utility tariff (OpenEI-style) with its effective date and price ranges.

    Mock only until v8: it always reads the saved case file, even in a live run, and the harness
    marks it 'mock_data_in_live_run' so the plan never presents it as live data. The tariff is
    flagged for the user to confirm, because picking the wrong tariff skews savings widely.
    """
    return require_mock_or_fixture(case, "get_utility_tariff")
