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

    def reset(self) -> None:
        self._index = 0

    def next_step(
        self,
        *,
        system_prompt: str,
        user_message: str,
        notes_summary: str,
        tool_schemas: list[dict[str, Any]],
    ) -> LLMStep:
        if self._index >= len(self._steps):
            raise RuntimeError("Scripted LLM ran out of steps before write_roadmap.")

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
