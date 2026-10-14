"""
End-to-end harness test for case1 with scripted LLM (no network, no API key).
"""

from __future__ import annotations

import os

import pytest

from agent.harness import run_harness
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
