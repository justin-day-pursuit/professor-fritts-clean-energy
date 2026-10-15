"""
Anthropic Claude client with tool-use for the harness (live path when a key is set).

Without ANTHROPIC_API_KEY the harness catches LLMConfigurationError and shows one plain sentence.
"""

from __future__ import annotations

import json
import os
from typing import Any

from agent.claims import WriteAnswerInput, WriteRoadmapInput
from agent.llm.base import LLMCallError, LLMClient, LLMConfigurationError, LLMStep

# Default model when ANTHROPIC_MODEL is blank — update from Anthropic docs when upgrading.
# The previous default (claude-3-5-sonnet-20241022) was retired and returned a 404 on every call.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"

# A full 13-section roadmap is far longer than the old 4096-token cap, which cut it off mid-answer.
DEFAULT_MAX_TOKENS = 16000


def _model_id() -> str:
    """Read the Claude model id from the environment, or use the code default."""
    return os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_ANTHROPIC_MODEL


def _max_tokens() -> int:
    """Longest answer one model call may write; ANTHROPIC_MAX_TOKENS in .env overrides the default."""
    raw = os.environ.get("ANTHROPIC_MAX_TOKENS", "").strip()
    return int(raw) if raw.isdigit() and int(raw) > 0 else DEFAULT_MAX_TOKENS


def _call_error(exc: Exception, model: str) -> LLMCallError:
    """
    Turn an Anthropic SDK error into one plain sentence for the run log.

    Without this the SDK error is not a RuntimeError, so it escapes the harness and crashes the request.
    The message never includes the API key.
    """
    import anthropic

    if isinstance(exc, anthropic.NotFoundError):
        return LLMCallError(f"Model {model!r} was not found. Set ANTHROPIC_MODEL in .env to a current model id.")
    if isinstance(exc, anthropic.AuthenticationError):
        return LLMCallError("Anthropic rejected the API key. Check ANTHROPIC_API_KEY in .env.")
    if isinstance(exc, anthropic.RateLimitError):
        return LLMCallError("Anthropic rate limit reached. Wait a moment and try again.")
    if isinstance(exc, anthropic.APIConnectionError):
        return LLMCallError("Could not reach the Anthropic API (network problem or timeout). Try again.")
    status = getattr(exc, "status_code", None)
    return LLMCallError(f"Anthropic API error (HTTP {status}): {getattr(exc, 'message', exc)}")


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
        # tool_use ids the model asked for beyond the first one; each still needs a tool_result.
        self._skipped_tool_use_ids: list[str] = []

    def reset(self) -> None:
        """Clear conversation history for a new harness run."""
        self._messages = []
        self._skipped_tool_use_ids = []

    def submit_tool_result(self, tool_use_id: str, payload: str, notes_summary: str) -> None:
        """
        Append the real tool JSON and fresh notes before the next model call.

        The harness calls this after execute_tool — never use a generic stub string here.
        """
        content: list[dict[str, Any]] = [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": payload,
            }
        ]
        # The API rejects the next call unless EVERY tool_use in the last answer gets a tool_result.
        # We ask for one tool per turn, but if extras still arrive, tell the model they did not run.
        for skipped_id in self._skipped_tool_use_ids:
            content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": skipped_id,
                    "content": "Not run: only one tool can be called at a time. Call it again if you still need it.",
                    "is_error": True,
                }
            )
        self._skipped_tool_use_ids = []
        self._messages.append({"role": "user", "content": content})
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
        """
        Ask Claude for the next step and translate its reply into one LLMStep.

        Sends at most one tool call per turn, allows a long answer, and turns SDK failures and
        cut-off answers into LLMCallError so the harness can end the run with a readable message.
        """
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

        model = _model_id()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=_max_tokens(),
                system=system_prompt,
                messages=self._messages,
                tools=tools,
                # At most one tool call per turn: the harness runs and answers one tool at a time.
                # Without this, newer models ask for several at once and the next request is rejected.
                tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            )
        except anthropic.APIError as exc:
            raise _call_error(exc, model) from exc

        if response.stop_reason == "max_tokens":
            # The answer (often the roadmap) was cut off, so any tool input in it is incomplete.
            # Stop here instead of passing an empty roadmap on to Check 4.
            raise LLMCallError(
                f"The model's answer was cut off at {_max_tokens()} tokens. "
                "Raise ANTHROPIC_MAX_TOKENS in .env and try again."
            )

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        self._skipped_tool_use_ids = [block.id for block in tool_uses[1:]]
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
