"""Prove the service layer and sync_to_async wrappers can create runs and events."""

import pytest

from core import services
from core.models import Run


@pytest.mark.asyncio
async def test_session_run_and_events_via_async_services():
    """
    Create a session and run through async helpers, append three events, then finish the run.

    This mirrors how FastAPI routes will call the ORM without blocking the event loop.
    """
    session = await services.create_session_async(profile={"address": "Test Library"})
    run = await services.create_run_async(
        session,
        tool_mode="mock",
        llm_provider="scripted",
        status=Run.Status.RUNNING,
    )

    for seq, kind in enumerate(["check1", "think", "tool_call"], start=1):
        await services.append_event_async(run, seq=seq, kind=kind, payload={"step": seq})

    finished = await services.finish_run_async(
        run,
        status=Run.Status.DONE,
        output={"answer": "v0 stand-in"},
        tool_call_count=1,
        elapsed_seconds=0.5,
    )

    loaded = await services.get_run_with_events_async(finished.id)
    assert loaded.status == Run.Status.DONE
    assert loaded.events.count() == 3
    kinds = [event.kind for event in loaded.events.all()]
    assert kinds == ["check1", "think", "tool_call"]
