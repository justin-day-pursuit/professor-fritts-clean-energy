"""
Anthropic Claude client with tool-use for the harness (live path when a key is set).

Without ANTHROPIC_API_KEY the harness catches LLMConfigurationError and shows one plain sentence.
"""

from __future__ import annotations

import json
import os
from typing import Any

from agent.claims import WriteAnswerInput, WriteRoadmapInput
from agent.llm.base import LLMClient, LLMConfigurationError, LLMStep

# Default model when ANTHROPIC_MODEL is blank — update from Anthropic docs when upgrading.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"


def _model_id() -> str:
    """Read the Claude model id from the environment, or use the code default."""
    return os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_ANTHROPIC_MODEL


def _final_tool_schemas() -> list[dict[str, Any]]:
    """
    Tool definitions for write_roadmap and write_answer using the same Pydantic models as Check 4.

    Keeps the API schema aligned with WriteRoadmapInput / WriteAnswerInput — not registry tools.
    """
    return [
        {
            "name": "write_roadmap",
            "description": "Submit the full v0 priority roadmap with labeled claims.",
            "input_schema": WriteRoadmapInput.model_json_schema(),
        },
        {
            "name": "write_answer",
            "description": "Submit a follow-up answer with labeled claims.",
            "input_schema": WriteAnswerInput.model_json_schema(),
        },
    ]


class AnthropicLLM(LLMClient):
    """
    Calls the Anthropic Messages API with tool definitions derived from the registry.

    Requires ANTHROPIC_API_KEY in the root .env; never log the key value.
    """

    def __init__(self) -> None:
        self._messages: list[dict[str, Any]] = []

    def reset(self) -> None:
        """Clear conversation history for a new harness run."""
        self._messages = []

    def submit_tool_result(self, tool_use_id: str, payload: str, notes_summary: str) -> None:
        """
        Append the real tool JSON and fresh notes before the next model call.

        The harness calls this after execute_tool — never use a generic stub string here.
        """
        self._messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": payload,
                    }
                ],
            }
        )
        if notes_summary.strip():
            self._messages.append(
                {
                    "role": "user",
                    "content": f"Updated working notes:\n{notes_summary}",
                }
            )

    def next_step(
        self,
        *,
        system_prompt: str,
        user_message: str,
        notes_summary: str,
        tool_schemas: list[dict[str, Any]],
        fix_context: str | None = None,
    ) -> LLMStep:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise LLMConfigurationError(
                "Paste your ANTHROPIC_API_KEY into .env at the project root, then try again."
            )

        try:
            import anthropic
        except ImportError as exc:
            raise LLMConfigurationError("Anthropic SDK is not installed.") from exc

        client = anthropic.Anthropic(api_key=api_key)
        if not self._messages:
            self._messages.append(
                {
                    "role": "user",
                    "content": f"{user_message}\n\n{notes_summary}",
                }
            )

        if fix_context:
            self._messages.append({"role": "user", "content": fix_context})

        tools = tool_schemas + _final_tool_schemas()

        response = client.messages.create(
            model=_model_id(),
            max_tokens=4096,
            system=system_prompt,
            messages=self._messages,
            tools=tools,
        )

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if not tool_uses:
            text = "".join(getattr(b, "text", "") for b in response.content if hasattr(b, "text"))
            # Keep text-only replies in history so the model does not repeat itself blindly.
            self._messages.append({"role": "assistant", "content": response.content})
            return LLMStep(kind="think", message=text or "Continuing analysis.")

        block = tool_uses[0]
        name = block.name
        tool_input = block.input if isinstance(block.input, dict) else json.loads(block.input)

        self._messages.append({"role": "assistant", "content": response.content})
        # Tool results are added later via submit_tool_result when the harness has real data.

        if name in ("write_roadmap", "write_answer"):
            # Keep tool_use_id so the harness can answer this tool_use before a Check 4 retry.
            return LLMStep(
                kind="final",
                tool_name=name,
                tool_input=tool_input,
                tool_use_id=block.id,
            )
        return LLMStep(kind="tool", tool_name=name, tool_input=tool_input, tool_use_id=block.id)
