"""
Run limits from environment — tool calls, retries, and wall-clock timeout.

These mirror the orange Check 2 boxes in the agent-flow diagram.
"""

from __future__ import annotations

import os
import time

from django.conf import settings


def tool_call_limit() -> int:
    """Maximum tool invocations per user message (default 40)."""
    raw = os.environ.get("TOOL_CALL_LIMIT") or getattr(settings, "TOOL_CALL_LIMIT", "40")
    return int(raw)


def tool_retry_limit() -> int:
    """Maximum retries per tool name when the LLM repeats a failed call (default 2)."""
    raw = os.environ.get("TOOL_RETRY_LIMIT") or getattr(settings, "TOOL_RETRY_LIMIT", "2")
    return int(raw)


def run_timeout_seconds() -> float:
    """Wall-clock budget for one harness run (default 600 seconds)."""
    raw = os.environ.get("RUN_TIMEOUT_SECONDS") or getattr(settings, "RUN_TIMEOUT_SECONDS", "600")
    return float(raw)


class RunLimits:
    """
    Mutable counters for one run — the harness updates these before each tool call.

    Reset by creating a new instance at the start of run().
    """

    def __init__(self) -> None:
        self.tool_call_count = 0
        self.retries_by_tool: dict[str, int] = {}
        self.started_at = time.monotonic()

    def elapsed(self) -> float:
        return time.monotonic() - self.started_at

    def timeout_exceeded(self) -> bool:
        return self.elapsed() > run_timeout_seconds()

    def record_tool_call(self, tool_name: str) -> None:
        self.tool_call_count += 1
        self.retries_by_tool[tool_name] = self.retries_by_tool.get(tool_name, 0) + 1
