"""
Load saved tool JSON for tools that run from fixtures (TOOL_MODE=mock, or live tools not built yet).

Fixture files live under mocks/fixtures/<case>/<tool_name>.json and mirror ToolResult fields.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from django.conf import settings

from tools.base import ToolResult, ToolUnavailableError

FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"


# A mode forced for the current request only (v6). The replay endpoint uses it so a saved demo always reads its
# saved tool answers, even on a server set to live, without changing the setting other requests are using.
_forced_tool_mode: ContextVar[str | None] = ContextVar("forced_tool_mode", default=None)


@contextmanager
def forced_tool_mode(mode: str) -> Iterator[None]:
    """Make get_tool_mode() return this mode inside the with-block, for this request only."""
    token = _forced_tool_mode.set(mode.strip().lower())
    try:
        yield
    finally:
        _forced_tool_mode.reset(token)


def get_tool_mode() -> str:
    """Read TOOL_MODE from a forced mode, Django settings or the environment (default mock)."""
    forced = _forced_tool_mode.get()
    if forced:
        return forced
    return getattr(settings, "TOOL_MODE", os.environ.get("TOOL_MODE", "mock")).strip().lower()


def fixture_path(case: str, tool_name: str) -> Path:
    """Path to the JSON file for one tool in one eval case."""
    return FIXTURES_ROOT / case / f"{tool_name}.json"


def load_fixture(case: str, tool_name: str) -> ToolResult:
    """
    Read a fixture file and return a ToolResult.

    Each fixture must include source_url, retrieved_at, dataset_version, and mock: true.
    A fixture with a top-level "error" key records a tool outage instead (v6, eval case 3):
    loading it raises ToolUnavailableError with that message, the same way a failed live call would.
    """
    path = fixture_path(case, tool_name)
    if not path.exists():
        raise FileNotFoundError(f"No mock fixture at {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("error"):
        raise ToolUnavailableError(str(raw["error"]))
    return ToolResult.model_validate(raw)


def require_mock_or_fixture(case: str, tool_name: str) -> ToolResult:
    """
    Return the saved fixture for a tool that has no live version yet.

    In live mode these tools still answer from fixtures; the result keeps mock: true,
    so the run log and the roadmap can tell which numbers are not real data.
    """
    return load_fixture(case, tool_name)
