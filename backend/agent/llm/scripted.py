"""
Scripted LLM — replays tool calls from fixtures/<case>/scripted_llm.json.

Tests and run_case --llm scripted use this path with no API key or network.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.llm.base import LLMClient, LLMStep

FIXTURES_ROOT = Path(__file__).resolve().parent.parent.parent / "mocks" / "fixtures"


class ScriptedLLM(LLMClient):
    """
    Walks a fixed list of steps from JSON — deterministic harness regression.

    To change case behavior, edit scripted_llm.json in the case folder, not this class.
    """

    def __init__(self, case: str) -> None:
        path = FIXTURES_ROOT / case / "scripted_llm.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        self._steps: list[dict[str, Any]] = raw.get("steps", raw)
        self._index = 0
        self._replay_final_once = False
        self._last_final_step: dict[str, Any] | None = None
        for step in reversed(self._steps):
            if step.get("type") == "final":
                self._last_final_step = step
                break

    def reset(self) -> None:
        """Rewind to the first scripted step for a new run."""
        self._index = 0
        self._replay_final_once = False

    def prepare_check4_retry(self, issues: list[str], user_message: str) -> None:
        """
        After Check 4 fails, allow one more final step instead of raising out-of-steps.

        If the main sequence is finished, the next next_step replays the last write_roadmap once.
        """
        _ = user_message
        if issues:
            pass  # Issues are already in harness notes flags; replay uses the same fixture final.
        if self._index >= len(self._steps) and self._last_final_step:
            self._replay_final_once = True

    def next_step(
        self,
        *,
        system_prompt: str,
        user_message: str,
        notes_summary: str,
        tool_schemas: list[dict[str, Any]],
        fix_context: str | None = None,
    ) -> LLMStep:
        _ = (system_prompt, user_message, notes_summary, tool_schemas, fix_context)

        if self._replay_final_once and self._last_final_step:
            self._replay_final_once = False
            step = self._last_final_step
            return LLMStep(
                kind="final",
                tool_name=step.get("name", "write_roadmap"),
                tool_input=step.get("input", {}),
            )

        if self._index >= len(self._steps):
            # Signal exhaustion so the harness can finish partial without an uncaught exception.
            return LLMStep(
                kind="exhausted",
                message="Scripted sequence finished without a passing Check 4 fix.",
            )

        step = self._steps[self._index]
        self._index += 1
        step_type = step.get("type", "tool")
        if step_type == "think":
            return LLMStep(kind="think", message=step.get("message", "Thinking…"))
        if step_type == "final":
            return LLMStep(
                kind="final",
                tool_name=step.get("name", "write_roadmap"),
                tool_input=step.get("input", {}),
            )
        return LLMStep(
            kind="tool",
            tool_name=step["name"],
            tool_input=step.get("input", {}),
        )
