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
from agent.llm.pricing import estimate_cost_usd

# Default model when ANTHROPIC_MODEL is blank — update from Anthropic docs when upgrading.
# The previous default (claude-3-5-sonnet-20241022) was retired and returned a 404 on every call.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"

# A full 13-section roadmap is far longer than the old 4096-token cap, which cut it off mid-answer.
DEFAULT_MAX_TOKENS = 16000


def _model_id() -> str:
    """Read the Claude model id from the environment, or use the code default."""
    return os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_ANTHROPIC_MODEL


def prompt_cache_enabled() -> bool:
    """Prompt caching is on unless ANTHROPIC_PROMPT_CACHE is set to 0, false, off or no in .env."""
    return os.environ.get("ANTHROPIC_PROMPT_CACHE", "1").strip().lower() not in ("0", "false", "off", "no")


def with_cache_marker(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    A copy of the conversation with a cache marker on the end of its last message (v6).

    The marker tells Claude to remember everything up to there, so the next call, which starts with the same
    conversation, reads it from the cache. The stored history is never changed (markers piling up in it would
    pass the limit of four per request), and only the last message is copied.
    """
    if not messages:
        return messages
    marker = {"type": "ephemeral"}
    last = messages[-1]
    content = last["content"]
    if isinstance(content, str):
        marked: Any = [{"type": "text", "text": content, "cache_control": marker}]
    else:
        blocks = list(content)
        tail = blocks[-1]
        # Tool results are plain dicts; model replies are SDK objects, which are not marked (the last message
        # is a user message when this is called, so that case is only a safeguard).
        if isinstance(tail, dict):
            blocks[-1] = {**tail, "cache_control": marker}
        marked = blocks
    return [*messages[:-1], {**last, "content": marked}]


def usage_record(model: str, usage: Any) -> dict[str, Any] | None:
    """The token counts of one reply as a plain dict with the estimated dollars, or None if the reply had none."""
    if usage is None:
        return None
    record: dict[str, Any] = {
        "model": model,
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "cache_creation_input_tokens": int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
        "cache_read_input_tokens": int(getattr(usage, "cache_read_input_tokens", 0) or 0),
    }
    record["estimated_usd"] = estimate_cost_usd(model, record)
    return record


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
        # Token counts of the last reply, waiting for the harness to save them (see take_usage).
        self._pending_usage: dict[str, Any] | None = None
        self._cache_ok = prompt_cache_enabled()

    def reset(self) -> None:
        """Clear conversation history for a new harness run."""
        self._messages = []
        self._skipped_tool_use_ids = []
        self._pending_usage = None
        self._cache_ok = prompt_cache_enabled()

    def take_usage(self) -> dict[str, Any] | None:
        """The token counts and estimated cost of the last model call, once; the harness saves them as a run event."""
        usage, self._pending_usage = self._pending_usage, None
        return usage

    def _create_message(self, client: Any, anthropic: Any, model: str, system_prompt: str, tools: list[dict[str, Any]]) -> Any:
        """
        Send the conversation to Claude, with prompt-cache markers when they are switched on (v6).

        Every call re-sends the system prompt, the tool list and the whole conversation so far. Marking the end
        of the system prompt and tools, and the end of the conversation, lets the next call read that part
        from the cache at a tenth of the price. If Anthropic rejects the markers, the call is repeated once
        without them and caching stays off for the rest of the run, so a caching problem can never stop a plan.
        The token counts of the reply are kept for take_usage().
        """
        use_cache = getattr(self, "_cache_ok", True)
        try:
            response = self._send(client, model, system_prompt, tools, use_cache)
        except anthropic.BadRequestError as exc:
            if not use_cache or "cache_control" not in str(exc):
                raise _call_error(exc, model) from exc
            self._cache_ok = False
            try:
                response = self._send(client, model, system_prompt, tools, False)
            except anthropic.APIError as retry_exc:
                raise _call_error(retry_exc, model) from retry_exc
        except anthropic.APIError as exc:
            raise _call_error(exc, model) from exc
        self._pending_usage = usage_record(model, getattr(response, "usage", None))
        return response

    def _send(self, client: Any, model: str, system_prompt: str, tools: list[dict[str, Any]], use_cache: bool) -> Any:
        """One messages.create call; use_cache adds the cache markers to a copy of the request, never to the history."""
        if use_cache:
            system: Any = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
            messages = with_cache_marker(self._messages)
        else:
            system, messages = system_prompt, self._messages
        return client.messages.create(
            model=model,
            max_tokens=_max_tokens(),
            system=system,
            messages=messages,
            tools=tools,
            # At most one tool call per turn: the harness runs and answers one tool at a time.
            # Without this, newer models ask for several at once and the next request is rejected.
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
        )

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
        response = self._create_message(client, anthropic, model, system_prompt, tools)

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
