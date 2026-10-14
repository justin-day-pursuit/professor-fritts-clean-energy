"""
End-to-end harness test for case1 with scripted LLM (no network, no API key).
"""

from __future__ import annotations

import os

import pytest

from typing import Any

from agent.claims import Claim, RoadmapPayload, RoadmapSection
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
    tool_calls = [e for e in run.events.all() if e.kind == "tool_call"]
    tool_results = [e for e in run.events.all() if e.kind == "tool_result"]
    assert len(tool_calls) >= 3
    assert len(tool_results) == len(tool_calls)

    md = (run.output or {}).get("markdown", "")
    assert "FACT" in md or "ESTIMATE" in md
    assert "structural" in md.lower() or "PE/RA" in md
    assert "does not reach" in md.lower() or "19%" in md


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
        good = RoadmapPayload(
            sections=[
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
            ]
        )
        return LLMStep(
            kind="final",
            tool_name="write_roadmap",
            tool_input={"roadmap": good.model_dump()},
            tool_use_id="toolu_check4_retry_test_2",
        )


def test_harness_submits_tool_result_before_check4_retry(monkeypatch):
    fake = _Check4RetryRecordingLLM()
    monkeypatch.setattr("agent.harness.get_llm_client", lambda _provider, fixture_case=None: fake)

    profile = {"state": "NY", "budget_amount": 100, "goal": "cut 30%"}
    session = services.create_session(profile=profile)
    run = run_harness(session, "retry test", llm_provider="anthropic")

    assert len(fake.submit_calls) == 1
    assert fake.submit_calls[0][0] == "toolu_check4_retry_test"
    assert "check4_issues" in fake.submit_calls[0][1]
    assert run.status == Run.Status.DONE
