"""
Start a run in the background, then check on it (v8, for the design page).

A real analysis takes about two minutes, which is too long to hold one web request open: browsers and the hosting
proxy can give up first. So the design page does this instead:

  POST /api/sessions/{id}/runs        starts the run on a background thread and answers at once (202).
  GET  /api/sessions/{id}/latest-run  the newest run for the session, with the steps it has taken so far. The page asks
                                      every couple of seconds, shows the real steps as they happen, and shows the plan
                                      when the status is no longer "running".

The older POST /api/sessions/{id}/messages (the classic planner) still waits for the whole run and is unchanged.

Real runs spend Claude credits, so starting one is limited: one at a time per session, and a daily cap across the site
(LIVE_RUNS_PER_DAY, default 25). Runs on the scripted model, which cost nothing, are never counted or capped.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, time, timezone
from uuid import UUID

from django.conf import settings
from django.db import connection
from fastapi import APIRouter, HTTPException

from agent.harness import run_harness
from api import schemas
from core import services
from core.models import Run

router = APIRouter(prefix="/sessions", tags=["live-runs"])
log = logging.getLogger(__name__)

# Sessions that have a run going in this server process, so a double click cannot start two paid runs at once.
_active: set[UUID] = set()
_active_lock = threading.Lock()

DEFAULT_RUNS_PER_DAY = 25


def _server_llm_provider() -> str:
    """The model follows the server's own setting, as for the chat route; a request cannot choose it."""
    return getattr(settings, "LLM_PROVIDER", "anthropic")


def runs_per_day() -> int:
    """The daily cap on real (paid) runs; 0 or a bad value falls back to the default."""
    try:
        value = int(os.environ.get("LIVE_RUNS_PER_DAY", DEFAULT_RUNS_PER_DAY))
    except ValueError:
        return DEFAULT_RUNS_PER_DAY
    return value if value > 0 else DEFAULT_RUNS_PER_DAY


def paid_runs_today() -> int:
    """How many real-Claude runs were started since midnight UTC."""
    midnight = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)
    return Run.objects.filter(llm_provider="anthropic", created_at__gte=midnight).count()


def _work(session_id: UUID, content: str, provider: str) -> None:
    """Run the agent for one session on a background thread, then let go of the session and the database connection."""
    try:
        session = services.get_session(session_id)
        run_harness(session, content, llm_provider=provider)
    except Exception:  # the harness records its own failures; this only guards the thread itself
        log.exception("Background run for session %s crashed", session_id)
    finally:
        with _active_lock:
            _active.discard(session_id)
        connection.close()


@router.post("/{session_id}/runs", response_model=schemas.LiveRunStartResponse, status_code=202)
def start_run(session_id: UUID, body: schemas.MessageCreateRequest):
    """
    Start a run for the session's saved profile and question, and return straight away.

    Answers 404 for an unknown session, 409 if this session already has a run going, and 429 when the daily cap
    on real runs has been reached (the message says so in plain words). A plain `def` so FastAPI runs the database
    work in a worker thread.
    """
    try:
        session = services.get_session(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    provider = _server_llm_provider()
    if provider == "anthropic" and paid_runs_today() >= runs_per_day():
        raise HTTPException(
            status_code=429,
            detail="Professor Fritts has done as many live analyses as he can for today. Please try again tomorrow, or open one of the sample plans.",
        )

    with _active_lock:
        if session_id in _active:
            raise HTTPException(status_code=409, detail="A run for this session is already going.")
        _active.add(session_id)

    try:
        services.add_message(session, role="user", content=body.content)
        threading.Thread(target=_work, args=(session_id, body.content, provider), daemon=True, name=f"run-{session_id}").start()
    except Exception:
        with _active_lock:
            _active.discard(session_id)
        raise
    return schemas.LiveRunStartResponse(session_id=session_id, started=True)


@router.get("/{session_id}/latest-run", response_model=schemas.RunResponse)
def latest_run(session_id: UUID):
    """The newest run for the session with its steps so far, or 404 if the run has not been created yet (ask again)."""
    run = (
        Run.objects.filter(session_id=session_id)
        .prefetch_related("events")
        .order_by("-id")
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="No run yet for this session")
    return schemas.run_to_response(run)
