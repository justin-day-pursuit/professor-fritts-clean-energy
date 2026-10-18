"""
Abstract LLM interface — returns the next tool call or final structured answer.

Implementations: scripted (fixtures) and anthropic (Claude with tool use).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMStep:
    """One model turn: tool call, final write_*, think text, or scripted exhaustion."""

    kind: str  # "tool" | "final" | "think" | "exhausted"
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    message: str | None = None
    # Anthropic tool_use block id — harness sends the real result before the next step.
    tool_use_id: str | None = None


class LLMClient(ABC):
    """Provider-selected client; the harness calls next_step until a final tool appears."""

    @abstractmethod
    def next_step(
        self,
        *,
        system_prompt: str,
        user_message: str,
        notes_summary: str,
        tool_schemas: list[dict[str, Any]],
        fix_context: str | None = None,
    ) -> LLMStep:
        """Return the next action; raise LLMConfigurationError when setup is invalid."""

    @abstractmethod
    def reset(self) -> None:
        """Clear scripted cursor or conversation state between runs."""

    def prepare_check4_retry(self, issues: list[str], user_message: str) -> None:
        """
        Optional hook when Check 4 fails once — scripted LLM may replay a corrective step.

        Default no-op; override in scripted (and anthropic if needed).
        """

    def take_usage(self) -> dict | None:
        """
        Token counts and estimated cost of the last model call, or None (v6).

        The scripted model makes no API call, so it has none. The Anthropic client returns each reply's counts
        once; the harness saves them as a "usage" run event so spend can be seen without the Anthropic console.
        """
        return None

    def submit_tool_result(self, tool_use_id: str, payload: str, notes_summary: str) -> None:
        """
        Optional hook after the harness runs a tool — Anthropic needs the real JSON here.

        Default no-op for scripted mode.
        """


class LLMCallError(RuntimeError):
    """
    The model call itself failed: wrong model id, bad key, rate limit, outage, or an answer cut off.

    It is a RuntimeError on purpose: the harness already catches RuntimeError around next_step and
    closes the run with this message instead of crashing the request.
    """


class LLMConfigurationError(Exception):
    """User-facing configuration problem (for example missing API key)."""

    def user_message(self) -> str:
        return str(self)
