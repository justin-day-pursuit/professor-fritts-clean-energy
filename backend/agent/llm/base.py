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
    """One model turn: either invoke a tool or emit the final write_* payload."""

    kind: str  # "tool" | "final" | "think"
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    message: str | None = None


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
    ) -> LLMStep:
        """Return the next action; raise LLMConfigurationError when setup is invalid."""

    @abstractmethod
    def reset(self) -> None:
        """Clear scripted cursor or conversation state between runs."""


class LLMConfigurationError(Exception):
    """User-facing configuration problem (for example missing API key)."""

    def user_message(self) -> str:
        return str(self)
