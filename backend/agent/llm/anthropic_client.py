"""
Anthropic Claude client with tool-use for the harness (live path when a key is set).

Without ANTHROPIC_API_KEY the harness catches LLMConfigurationError and shows one plain sentence.
"""

from __future__ import annotations

import json
import os
from typing import Any

from agent.llm.base import LLMClient, LLMConfigurationError, LLMStep

# Default model when ANTHROPIC_MODEL is blank — update from Anthropic docs when upgrading.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"


def _model_id() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_ANTHROPIC_MODEL


class AnthropicLLM(LLMClient):
    """
    Calls the Anthropic Messages API with tool definitions derived from the registry.

    Requires ANTHROPIC_API_KEY in the root .env; never log the key value.
    """

    def __init__(self) -> None:
        self._messages: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._messages = []

    def next_step(
        self,
        *,
        system_prompt: str,
        user_message: str,
        notes_summary: str,
        tool_schemas: list[dict[str, Any]],
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

        final_tools = [
            {
                "name": "write_roadmap",
                "description": "Submit the full v0 priority roadmap with labeled claims.",
                "input_schema": tool_schemas[-2]["input_schema"]
                if len(tool_schemas) >= 2
                else {"type": "object", "properties": {"roadmap": {"type": "object"}}},
            },
            {
                "name": "write_answer",
                "description": "Submit a follow-up answer with labeled claims.",
                "input_schema": {"type": "object", "properties": {"summary": {"type": "string"}, "claims": {"type": "array"}}},
            },
        ]
        tools = tool_schemas + final_tools

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
            return LLMStep(kind="think", message=text or "Continuing analysis.")

        block = tool_uses[0]
        name = block.name
        tool_input = block.input if isinstance(block.input, dict) else json.loads(block.input)

        self._messages.append({"role": "assistant", "content": response.content})
        self._messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Tool executed by harness; see notes.",
                    }
                ],
            }
        )

        if name in ("write_roadmap", "write_answer"):
            return LLMStep(kind="final", tool_name=name, tool_input=tool_input)
        return LLMStep(kind="tool", tool_name=name, tool_input=tool_input)
