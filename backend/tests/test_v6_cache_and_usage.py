"""
Tests for prompt caching and spend logging in the Anthropic client (v6).

Caching marks the end of the system prompt and of the conversation so Claude's repeat reads are billed at a
tenth of the price. Spend logging saves each reply's token counts and an estimated dollar cost with the run.

Nothing here calls the real API. A fake client stands in for Anthropic, so these tests cost nothing, and they
show only that the request is built as intended: whether Anthropic honors it is confirmed only by a live run.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import anthropic
import httpx
import pytest

from agent import harness
from agent.harness import run_harness
from agent.llm.anthropic_client import AnthropicLLM, prompt_cache_enabled, usage_record, with_cache_marker
from agent.llm.base import LLMCallError, LLMStep
from agent.llm.pricing import estimate_cost_usd, sum_usage
from core import services
from core.models import Run
from tests.test_v6_hardening import _StubLLM, _stub_run

MODEL = "claude-sonnet-5-5"
MARKER = {"type": "ephemeral"}


# --- the cache marker on a copy of the conversation -----------------------------------------------


def test_marker_goes_on_the_end_of_the_last_message_and_history_is_untouched():
    """A text message becomes one marked block; the stored history is never changed, so markers cannot pile up."""
    history = [
        {"role": "user", "content": "How can we cut power 30%?"},
        {"role": "assistant", "content": [SimpleNamespace(type="tool_use")]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "{}"}]},
        {"role": "user", "content": "Updated working notes: none"},
    ]
    before = repr(history)
    sent = with_cache_marker(history)
    assert sent[-1]["content"] == [{"type": "text", "text": "Updated working notes: none", "cache_control": MARKER}]
    assert sent[:-1] == history[:-1]
    assert repr(history) == before


def test_marker_on_tool_result_blocks_marks_only_the_last_block():
    """When the last message is tool results, only its final block carries the marker."""
    history = [
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "a", "content": "1"},
            {"type": "tool_result", "tool_use_id": "b", "content": "2"},
        ]},
    ]
    sent = with_cache_marker(history)
    assert "cache_control" not in sent[0]["content"][0]
    assert sent[0]["content"][1]["cache_control"] == MARKER
    assert "cache_control" not in history[0]["content"][1]


def test_marker_leaves_an_empty_conversation_alone():
    """With no messages there is nothing to mark."""
    assert with_cache_marker([]) == []


@pytest.mark.parametrize(("value", "expected"), [("", True), ("1", True), ("0", False), ("false", False), ("OFF", False), ("no", False)])
def test_caching_can_be_switched_off_in_the_environment(monkeypatch, value, expected):
    """ANTHROPIC_PROMPT_CACHE=0 (or false, off, no) turns caching off; anything else leaves it on."""
    monkeypatch.setenv("ANTHROPIC_PROMPT_CACHE", value)
    assert prompt_cache_enabled() is expected


# --- prices and usage records -----------------------------------------------------------------------


def test_cost_uses_the_published_prices():
    """One million of each kind at the Sonnet 5.5 prices: $2 in, $10 out, $0.20 cache read, $2.50 cache write."""
    usage = {"input_tokens": 1_000_000, "output_tokens": 1_000_000, "cache_read_input_tokens": 1_000_000, "cache_creation_input_tokens": 1_000_000}
    assert estimate_cost_usd(MODEL, usage) == pytest.approx(2.00 + 10.00 + 0.20 + 2.50)


def test_a_model_with_no_price_has_no_cost_instead_of_a_wrong_one():
    """An unlisted model gives None, never a guessed dollar figure."""
    assert estimate_cost_usd("claude-something-new", {"input_tokens": 1000}) is None


def test_usage_record_reads_the_reply_counts_and_tolerates_missing_cache_fields():
    """The counts come from the reply; a reply with no cache fields counts them as zero."""
    reply = SimpleNamespace(input_tokens=1200, output_tokens=300, cache_read_input_tokens=None)
    record = usage_record(MODEL, reply)
    assert record["input_tokens"] == 1200 and record["cache_read_input_tokens"] == 0 and record["cache_creation_input_tokens"] == 0
    assert record["estimated_usd"] == pytest.approx((1200 * 2 + 300 * 10) / 1_000_000, abs=1e-4)
    assert usage_record(MODEL, None) is None


def test_totals_add_up_calls_and_keep_no_cost_when_any_call_is_unpriced():
    """The run total sums every call, and says None for dollars when any call had no price."""
    priced = {"model": MODEL, "input_tokens": 100, "output_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 50, "estimated_usd": 0.001}
    unpriced = {**priced, "estimated_usd": None}
    assert sum_usage([priced, priced])["estimated_usd"] == 0.002 and sum_usage([priced, priced])["calls"] == 2
    assert sum_usage([priced, unpriced])["estimated_usd"] is None


# --- the client, with a fake Anthropic ----------------------------------------------------------------


class _FakeMessages:
    """Stands in for client.messages: records each request and answers from a list of replies or errors."""

    def __init__(self, answers: list[Any]) -> None:
        self.answers, self.requests = list(answers), []

    def create(self, **kwargs: Any) -> Any:
        self.requests.append(kwargs)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def _reply(tool: str = "get_building_profile", **usage: int) -> Any:
    """A fake Claude reply that asks for one tool, with the given token counts."""
    counts = {"input_tokens": 9000, "output_tokens": 120, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, **usage}
    block = SimpleNamespace(type="tool_use", id="toolu_1", name=tool, input={})
    return SimpleNamespace(content=[block], stop_reason="tool_use", usage=SimpleNamespace(**counts))


def _bad_request(message: str) -> anthropic.BadRequestError:
    """A 400 error like the one the API would send."""
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.BadRequestError(message, response=httpx.Response(400, request=request), body=None)


def _client_with(monkeypatch, answers: list[Any]) -> tuple[AnthropicLLM, _FakeMessages]:
    """An AnthropicLLM wired to a fake API that gives these answers, with a dummy key in the environment."""
    fake = _FakeMessages(answers)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: SimpleNamespace(messages=fake))
    llm = AnthropicLLM()
    llm.reset()
    return llm, fake


def _step(llm: AnthropicLLM, **kwargs: Any) -> LLMStep:
    """Ask the client for its next step with a tiny system prompt and no tool schemas."""
    return llm.next_step(system_prompt="You are a planner.", user_message="Plan it.", notes_summary="Notes.", tool_schemas=[], **kwargs)


def test_the_request_marks_the_system_prompt_and_the_conversation(monkeypatch):
    """With caching on, the system prompt is sent as a marked block and the last message carries a marker."""
    monkeypatch.delenv("ANTHROPIC_PROMPT_CACHE", raising=False)
    llm, fake = _client_with(monkeypatch, [_reply()])
    step = _step(llm)
    request = fake.requests[0]
    assert request["system"] == [{"type": "text", "text": "You are a planner.", "cache_control": MARKER}]
    assert request["messages"][-1]["content"][-1]["cache_control"] == MARKER
    assert step.kind == "tool" and step.tool_name == "get_building_profile"
    # The stored history has no markers in it.
    assert llm._messages[0]["content"] == "Plan it.\n\nNotes."


def test_a_request_with_caching_off_is_the_old_request(monkeypatch):
    """With caching switched off, the system prompt is plain text and no message is marked."""
    monkeypatch.setenv("ANTHROPIC_PROMPT_CACHE", "0")
    llm, fake = _client_with(monkeypatch, [_reply()])
    _step(llm)
    request = fake.requests[0]
    assert request["system"] == "You are a planner."
    # The same list the history is kept in is sent as it is (later replies get added to it), so check the first message.
    assert request["messages"][0]["content"] == "Plan it.\n\nNotes."


def test_if_anthropic_rejects_the_markers_the_call_is_repeated_without_them(monkeypatch):
    """A 400 that mentions cache_control triggers one retry with no markers, and caching stays off for the run."""
    monkeypatch.delenv("ANTHROPIC_PROMPT_CACHE", raising=False)
    llm, fake = _client_with(monkeypatch, [_bad_request("cache_control: extra inputs are not permitted"), _reply(), _reply()])
    _step(llm)
    assert len(fake.requests) == 2
    assert isinstance(fake.requests[0]["system"], list) and fake.requests[1]["system"] == "You are a planner."
    _step(llm)
    assert fake.requests[2]["system"] == "You are a planner."  # still off, no repeated failure


def test_other_bad_requests_are_not_retried_as_cache_problems(monkeypatch):
    """A 400 that has nothing to do with caching ends the call with a readable error, as before."""
    monkeypatch.delenv("ANTHROPIC_PROMPT_CACHE", raising=False)
    llm, fake = _client_with(monkeypatch, [_bad_request("messages: roles must alternate")])
    with pytest.raises(LLMCallError):
        _step(llm)
    assert len(fake.requests) == 1


def test_usage_is_handed_over_once_per_call(monkeypatch):
    """take_usage returns the last reply's counts and cost, then None until the next call."""
    llm, _ = _client_with(monkeypatch, [_reply(input_tokens=500, cache_read_input_tokens=8000)])
    _step(llm)
    usage = llm.take_usage()
    assert usage["input_tokens"] == 500 and usage["cache_read_input_tokens"] == 8000 and usage["model"] == MODEL
    assert usage["estimated_usd"] == pytest.approx((500 * 2 + 120 * 10 + 8000 * 0.2) / 1_000_000, abs=1e-4)
    assert llm.take_usage() is None


# --- usage saved with the run --------------------------------------------------------------------------


class _UsageStub(_StubLLM):
    """A model stub that reports a fixed usage record for every step, as the Anthropic client would."""

    def take_usage(self) -> dict[str, Any]:
        """The same counts for each call, so the run total is easy to check."""
        return {"model": MODEL, "input_tokens": 1000, "output_tokens": 100, "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 4000, "estimated_usd": 0.0038}


def test_a_run_saves_each_calls_usage_and_a_total(monkeypatch):
    """Each model call becomes a "usage" event, and the finished run carries the totals in its flags."""
    from mocks.catalog import load_case

    stub = _UsageStub([
        LLMStep(kind="tool", tool_name="get_building_profile", tool_input={}, tool_use_id="t1"),
        LLMStep(kind="tool", tool_name="get_hazard_context", tool_input={}, tool_use_id="t2"),
    ])
    monkeypatch.setattr(harness, "get_llm_client", lambda provider, fixture_case: stub)
    profile, question = load_case("case1_queens_library")
    session = services.create_session(profile=profile, fixture_case="case1_queens_library")
    run = services.get_run_with_events(run_harness(session, question, llm_provider="anthropic", tool_mode="mock").pk)
    usage_events = [e for e in run.events.all() if e.kind == "usage"]
    assert len(usage_events) == 3  # two tool calls, then the "exhausted" step, each is a model call
    assert run.flags["usage"]["calls"] == 3 and run.flags["usage"]["input_tokens"] == 3000
    assert run.flags["usage"]["estimated_usd"] == pytest.approx(0.0114)


def test_the_scripted_model_adds_no_usage_events():
    """The scripted model makes no API call, so a scripted run has no usage events and no usage flag."""
    from agent.evals import run_eval_case

    result = run_eval_case("case1_queens_library")
    assert result.passed
    run = Run.objects.order_by("-pk").first()
    assert not run.events.filter(kind="usage").exists() and "usage" not in (run.flags or {})
