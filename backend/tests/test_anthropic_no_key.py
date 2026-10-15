"""Anthropic mode without API key returns a plain sentence, not a stack trace."""

from __future__ import annotations

import os

import pytest

from agent.harness import run_harness
from core import services
from core.models import Run


def test_anthropic_missing_key_message(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    profile = {"state": "NY", "borough": "Queens", "budget_amount": 1, "goal": "cut"}
    session = services.create_session(profile=profile)
    run = run_harness(session, "hi", llm_provider="anthropic")
    run = services.get_run_with_events(run.pk)
    assert run.status == Run.Status.FAILED
    last = list(run.events.all())[-1]
    assert last.kind == "final"
    assert last.payload.get("ended") is True
    err = (run.output or {}).get("error", "")
    assert "ANTHROPIC_API_KEY" in err
    assert "Paste" in err or "paste" in err.lower()
