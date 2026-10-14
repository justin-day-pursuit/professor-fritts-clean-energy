"""
Solar production and storage optimization tools (group 2) — mock PVWatts and REopt in v0.
"""

from __future__ import annotations

from mocks.mock_mode import require_mock_or_fixture
from tools.base import ToolResult


def get_solar_production(case: str) -> ToolResult:
    """Return saved PVWatts-style annual production for the eval case."""
    return require_mock_or_fixture(case, "get_solar_production")


def optimize_solar_storage(case: str) -> ToolResult:
    """Return saved REopt-style battery sizing for critical-load hours."""
    return require_mock_or_fixture(case, "optimize_solar_storage")
