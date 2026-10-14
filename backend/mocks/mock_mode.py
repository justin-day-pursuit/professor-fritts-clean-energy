"""
Load saved tool JSON when TOOL_MODE=mock; refuse live external calls in v0.

Fixture files live under mocks/fixtures/<case>/<tool_name>.json and mirror ToolResult fields.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from django.conf import settings

from tools.base import ToolResult

FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"


class LiveModeNotAvailableError(RuntimeError):
    """Raised when TOOL_MODE=live — real APIs arrive in v1, not v0."""


def get_tool_mode() -> str:
    """Read TOOL_MODE from Django settings or the environment (default mock)."""
    return getattr(settings, "TOOL_MODE", os.environ.get("TOOL_MODE", "mock")).strip().lower()


def fixture_path(case: str, tool_name: str) -> Path:
    """Path to the JSON file for one tool in one eval case."""
    return FIXTURES_ROOT / case / f"{tool_name}.json"


def load_fixture(case: str, tool_name: str) -> ToolResult:
    """
    Read a fixture file and return a ToolResult.

    Each fixture must include source_url, retrieved_at, dataset_version, and mock: true.
    """
    path = fixture_path(case, tool_name)
    if not path.exists():
        raise FileNotFoundError(f"No mock fixture at {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ToolResult.model_validate(raw)


def require_mock_or_fixture(case: str, tool_name: str) -> ToolResult:
    """
    Return fixture data in mock mode, or raise if live mode was requested.

    This is the single gate so v0 never hits real energy APIs by accident.
    """
    mode = get_tool_mode()
    if mode == "live":
        raise LiveModeNotAvailableError(
            "Live tool mode is not available in v0. Set TOOL_MODE=mock in .env."
        )
    return load_fixture(case, tool_name)
