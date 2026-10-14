"""
Run limits from environment — tool calls, retries, and wall-clock timeout.

These mirror the orange Check 2 boxes in the agent-flow diagram.
"""

from __future__ import annotations

import os
import time

from django.conf import settings


def tool_call_limit() -> int:
    """Maximum successful tool invocations per user message (default 40)."""
    raw = os.environ.get("TOOL_CALL_LIMIT") or getattr(settings, "TOOL_CALL_LIMIT", "40")
    return int(raw)


def tool_retry_limit() -> int:
    """Maximum failed repeats per tool name before Check 2 blocks (default 2)."""
    raw = os.environ.get("TOOL_RETRY_LIMIT") or getattr(settings, "TOOL_RETRY_LIMIT", "2")
    return int(raw)


def run_timeout_seconds() -> float:
    """Wall-clock budget for one harness run (default 600 seconds)."""
    raw = os.environ.get("RUN_TIMEOUT_SECONDS") or getattr(settings, "RUN_TIMEOUT_SECONDS", "600")
    return float(raw)


# Stop endless think-only loops before the 600s run timeout.
MAX_CONSECUTIVE_THINK_STEPS = 5


class RunLimits:
    """
    Mutable counters for one run — the harness updates these around each tool call.

    Successful tools increment tool_call_count only; failures increment failed_attempts_by_tool.
    """

    def __init__(self) -> None:
        self.tool_call_count = 0
        self.failed_attempts_by_tool: dict[str, int] = {}
        self.started_at = time.monotonic()

    def elapsed(self) -> float:
        """Seconds since this run started (monotonic clock)."""
        return time.monotonic() - self.started_at

    def timeout_exceeded(self) -> bool:
        return self.elapsed() > run_timeout_seconds()

    def record_successful_tool_call(self, tool_name: str) -> None:
        """Count one completed tool toward the 40-call cap (not toward retry limit)."""
        self.tool_call_count += 1

    def record_failed_tool_attempt(self, tool_name: str) -> None:
        """Count a failed try so Check 2 can cap repeats of the same broken call."""
        self.failed_attempts_by_tool[tool_name] = self.failed_attempts_by_tool.get(tool_name, 0) + 1
