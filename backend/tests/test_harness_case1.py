"""
End-to-end harness test for case1 with scripted LLM (no network, no API key).
"""

from __future__ import annotations

import os

import pytest

from typing import Any

from agent.claims import Claim, RoadmapPayload, RoadmapSection, roadmap_with_sections
from agent.harness import run_harness
from agent.llm.base import LLMClient, LLMStep
from core import services
from core.models import Run


@pytest.fixture(autouse=True)
def scripted_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("TOOL_MODE", "mock")
    from django.conf import settings

    settings.LLM_PROVIDER = "scripted"
    settings.TOOL_MODE = "mock"


def test_harness_case1_scripted():
    profile = {
        "state": "NY",
        "borough": "Queens",
        "budget_amount": 400000,
        "goal": "Cut grid electricity 30% by 2030",
        "address": "41-17 Main Street",
        "annual_kwh": 310000,
    }
    session = services.create_session(profile=profile, fixture_case="case1_queens_library")
    msg = "How can we cut grid power 30% by 2030 on $400k?"
    run = run_harness(session, msg, llm_provider="scripted")
    run = services.get_run_with_events(run.pk)

    assert run.status in (Run.Status.DONE, Run.Status.PARTIAL)
    last = list(run.events.all())[-1]
    assert last.kind == "final"
    assert last.payload.get("ended") is True
    tool_calls = [e for e in run.events.all() if e.kind == "tool_call"]
    tool_results = [e for e in run.events.all() if e.kind == "tool_result"]
    assert len(tool_calls) >= 3
    assert len(tool_results) == len(tool_calls)

    md = (run.output or {}).get("markdown", "")
    assert "FACT" in md or "ESTIMATE" in md
    assert "structural" in md.lower() or "PE/RA" in md
    assert "does not reach" in md.lower() or "19%" in md


# A plain-words answer that passes the live-run check: live runs must open with one, and these stand-in plans pretend to be live.
_PLAIN_ANSWER = (
    "You asked how to reduce the building's grid electricity use. The plan finds that efficiency measures help but do not "
    "reach the goal on their own, and it says what limits the answer and what still needs to be confirmed. The roof, the "
    "tariff and the cost estimates all need review by the right professionals before any money is committed, and the plan "
    "lists who to contact and where to start. Nothing here is a promise of savings."
)


class _Check4RetryRecordingLLM(LLMClient):
    """
    Minimal fake LLM: first final fails Check 4, second passes; records tool_result calls.

    Used to prove the harness closes Anthropic tool_use before a Check 4 retry (no network).
    """

    def __init__(self) -> None:
        self.submit_calls: list[tuple[str, str]] = []
        self._final_attempt = 0

    def reset(self) -> None:
        self._final_attempt = 0
        self.submit_calls.clear()

    def submit_tool_result(self, tool_use_id: str, payload: str, notes_summary: str) -> None:
        _ = notes_summary
        self.submit_calls.append((tool_use_id, payload))

    def prepare_check4_retry(self, issues: list[str], user_message: str) -> None:
        _ = (issues, user_message)

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
        self._final_attempt += 1
        if self._final_attempt == 1:
            bad = RoadmapPayload(
                sections=[
                    RoadmapSection(
                        section_id="1",
                        title="Summary",
                        claims=[
                            Claim(
                                text="Missing provenance on purpose",
                                label="FACT",
                                confidence="high",
                            )
                        ],
                    )
                ]
            )
            return LLMStep(
                kind="final",
                tool_name="write_roadmap",
                tool_input={"roadmap": bad.model_dump()},
                tool_use_id="toolu_check4_retry_test",
            )
        good = roadmap_with_sections([
            RoadmapSection(
                section_id="1",
                title="Summary",
                claims=[
                    Claim(
                        text="Ok fact",
                        label="FACT",
                        confidence="high",
                        source_url="https://example.test/a",
                    )
                ],
            ),
            RoadmapSection(
                section_id="10",
                title="Referrals",
                claims=[
                    Claim(
                        text="PE/RA structural analysis required.",
                        label="RECOMMENDATION",
                        confidence="high",
                        source_url="session://profile",
                    ),
                    Claim(
                        text="Roof condition survey required.",
                        label="RECOMMENDATION",
                        confidence="high",
                        source_url="session://profile",
                    ),
                    Claim(
                        text="Licensed electrician for interconnection.",
                        label="RECOMMENDATION",
                        confidence="high",
                        source_url="session://profile",
                    ),
                    Claim(
                        text="FDNY rooftop access review.",
                        label="RECOMMENDATION",
                        confidence="high",
                        source_url="session://profile",
                    ),
                    Claim(
                        text="Con Edison utility interconnection review.",
                        label="RECOMMENDATION",
                        confidence="high",
                        source_url="session://profile",
                    ),
                ],
            ),
        ], plain_answer=_PLAIN_ANSWER)
        return LLMStep(
            kind="final",
            tool_name="write_roadmap",
            tool_input={"roadmap": good.model_dump()},
            tool_use_id="toolu_check4_retry_test_2",
        )


def test_harness_submits_tool_result_before_check4_retry(monkeypatch):
    """
    After a failed Check 4, the harness must close the Anthropic tool_use before retry.

    If the retry wiring moves, keep asserting one submit_tool_result with check4_issues in the payload.
    """
    fake = _Check4RetryRecordingLLM()
    monkeypatch.setattr("agent.harness.get_llm_client", lambda _provider, fixture_case=None: fake)

    profile = {"state": "NY", "borough": "Queens", "budget_amount": 100, "goal": "cut 30%"}
    session = services.create_session(profile=profile)
    run = run_harness(session, "retry test", llm_provider="anthropic")

    assert len(fake.submit_calls) == 1
    assert fake.submit_calls[0][0] == "toolu_check4_retry_test"
    assert "check4_issues" in fake.submit_calls[0][1]
    assert run.status == Run.Status.DONE


def _referral_claims_for_check4() -> list[Claim]:
    """
    Minimal referral claims so fake write_answer payloads pass Check 4 in this file.

    If mandatory referral keywords change in agent/checks.py, update the claim text here to match.
    """
    return [
        Claim(
            text="PE/RA structural analysis required.",
            label="RECOMMENDATION",
            confidence="high",
            source_url="session://profile",
        ),
        Claim(
            text="Roof condition survey required.",
            label="RECOMMENDATION",
            confidence="high",
            source_url="session://profile",
        ),
        Claim(
            text="Licensed electrician for interconnection.",
            label="RECOMMENDATION",
            confidence="high",
            source_url="session://profile",
        ),
        Claim(
            text="FDNY rooftop access review.",
            label="RECOMMENDATION",
            confidence="high",
            source_url="session://profile",
        ),
        Claim(
            text="Con Edison utility interconnection review.",
            label="RECOMMENDATION",
            confidence="high",
            source_url="session://profile",
        ),
    ]


class _WriteAnswerSummaryLLM(LLMClient):
    """Returns one write_answer final so we can assert the summary is stored."""

    def reset(self) -> None:
        pass

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
        summary = "Combine efficiency upgrades with solar; solar alone will not reach 30%."
        claims = [
            Claim(
                text="Budget remains USD 400,000 from intake.",
                label="FACT",
                confidence="high",
                source_url="session://profile",
            ),
            *_referral_claims_for_check4(),
        ]
        return LLMStep(
            kind="final",
            tool_name="write_answer",
            tool_input={"summary": summary, "claims": [c.model_dump() for c in claims]},
        )


def test_write_answer_summary_in_run_output(monkeypatch):
    """
    Follow-up runs must keep the write_answer summary in run output and markdown.

    If the harness stores summary under a different key or renderer, update the assertions here.
    """
    monkeypatch.setattr(
        "agent.harness.get_llm_client",
        lambda _provider, fixture_case=None: _WriteAnswerSummaryLLM(),
    )
    profile = {"state": "NY", "borough": "Queens", "budget_amount": 100, "goal": "cut 30%"}
    session = services.create_session(profile=profile)
    run = run_harness(session, "follow up", llm_provider="anthropic")

    expected = "Combine efficiency upgrades with solar; solar alone will not reach 30%."
    assert (run.output or {}).get("summary") == expected
    assert expected in (run.output or {}).get("markdown", "")
    assert run.status == Run.Status.DONE


class _ThinkCapAfterPayloadLLM(LLMClient):
    """
    First turn submits a failing final (payload exists), then think-only until the cap.

    Mirrors Check 4 fix loop followed by stuck thinking.
    """

    def __init__(self) -> None:
        self._step = 0

    def reset(self) -> None:
        self._step = 0

    def prepare_check4_retry(self, issues: list[str], user_message: str) -> None:
        _ = (issues, user_message)

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
        self._step += 1
        if self._step == 1:
            bad = RoadmapPayload(
                sections=[
                    RoadmapSection(
                        section_id="1",
                        title="Summary",
                        claims=[
                            Claim(
                                text="Missing provenance",
                                label="FACT",
                                confidence="high",
                            )
                        ],
                    )
                ]
            )
            return LLMStep(
                kind="final",
                tool_name="write_roadmap",
                tool_input={"roadmap": bad.model_dump()},
            )
        return LLMStep(kind="think", message=f"Stuck thinking step {self._step}")


def test_think_cap_after_payload_finishes_partial(monkeypatch):
    """
    After a roadmap exists, hitting the think cap should finish partial with flags, not failed.

    If partial think-cap flags or output shape change in the harness, adjust the status and flag checks here.
    """
    monkeypatch.setattr(
        "agent.harness.get_llm_client",
        lambda _provider, fixture_case=None: _ThinkCapAfterPayloadLLM(),
    )
    profile = {"state": "NY", "borough": "Queens", "budget_amount": 100, "goal": "cut 30%"}
    session = services.create_session(profile=profile)
    run = run_harness(session, "think cap test", llm_provider="anthropic")

    assert run.status == Run.Status.PARTIAL
    assert (run.flags or {}).get("think_cap_exceeded") is True
    assert "roadmap" in (run.output or {})
    assert "think_cap_exceeded" in (run.output or {}).get("notes", {}).get("flags", [])


def test_think_cap_without_payload_finishes_partial_no_roadmap(monkeypatch):
    """
    With no roadmap yet, the think cap should still finish partial and must not invent a roadmap.

    If the harness adds a different empty-payload shape, update the roadmap absence check here.
    """

    class _ThinkOnlyLLM(LLMClient):
        """
        Fake model that never calls a final tool — only think steps until the cap.

        Keep this in sync with MAX_CONSECUTIVE_THINK_STEPS in agent/limits.py if the cap changes.
        """

        def reset(self) -> None:
            pass

        def next_step(self, **kwargs: Any) -> LLMStep:
            _ = kwargs
            return LLMStep(kind="think", message="still thinking")

    monkeypatch.setattr(
        "agent.harness.get_llm_client",
        lambda _provider, fixture_case=None: _ThinkOnlyLLM(),
    )
    profile = {"state": "NY", "borough": "Queens", "budget_amount": 100, "goal": "cut 30%"}
    session = services.create_session(profile=profile)
    run = run_harness(session, "think only", llm_provider="anthropic")

    assert run.status == Run.Status.PARTIAL
    assert (run.flags or {}).get("think_cap_exceeded") is True
    assert "roadmap" not in (run.output or {})
