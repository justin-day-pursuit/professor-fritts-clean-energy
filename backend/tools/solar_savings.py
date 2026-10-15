"""
Solar production and storage optimization tools (group 2) — live PVWatts in v1, mock REopt.
"""

from __future__ import annotations

from typing import Any

from mocks.mock_mode import get_tool_mode, require_mock_or_fixture
from tools.base import ToolResult
from tools.live_solar import fetch_live_solar_production


def get_solar_production(
    case: str,
    profile: dict[str, Any] | None = None,
    system_kw: float | None = None,
) -> ToolResult:
    """Return live PVWatts output in live mode, or the saved fixture in mock mode."""
    if get_tool_mode() == "live":
        return fetch_live_solar_production(profile or {}, system_kw)
    return require_mock_or_fixture(case, "get_solar_production")


def optimize_solar_storage(case: str) -> ToolResult:
    """Return saved REopt-style battery sizing for critical-load hours."""
    return require_mock_or_fixture(case, "optimize_solar_storage")
