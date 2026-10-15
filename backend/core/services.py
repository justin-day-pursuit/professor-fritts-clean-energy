"""
Single doorway to the database for the API and agent harness.

Every create/read/update goes through these helpers so async FastAPI code can use the
sync_to_async wrappers without scattering ORM calls across the project.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async
from django.utils import timezone

from core.models import Document, Message, Run, RunEvent, Session


def create_session(
    profile: dict | None = None,
    status: str = "active",
    fixture_case: str = "case1_queens_library",
) -> Session:
    """Start a new planning session with an optional intake profile dict."""
    return Session.objects.create(
        profile=profile or {},
        status=status,
        fixture_case=fixture_case,
    )


def add_document(
    session: Session | UUID,
    *,
    filename: str,
    content_type: str,
    size_bytes: int,
    stored_path: str,
    parsed_summary: dict | None = None,
) -> Document:
    """Record an uploaded file and where it lives on disk."""
    if isinstance(session, UUID):
        session = Session.objects.get(pk=session)
    return Document.objects.create(
        session=session,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        stored_path=stored_path,
        parsed_summary=parsed_summary or {},
    )


def add_message(
    session: Session | UUID,
    *,
    role: str,
    content: str,
    run: Run | None = None,
) -> Message:
    """Append a chat message; link to a run when the harness produced it."""
    if isinstance(session, UUID):
        session = Session.objects.get(pk=session)
    return Message.objects.create(session=session, role=role, content=content, run=run)


def create_run(
    session: Session | UUID,
    *,
    tool_mode: str,
    llm_provider: str,
    status: str = Run.Status.QUEUED,
) -> Run:
    """Queue a new agent run for a session with the configured tool and LLM modes."""
    if isinstance(session, UUID):
        session = Session.objects.get(pk=session)
    return Run.objects.create(
        session=session,
        status=status,
        tool_mode=tool_mode,
        llm_provider=llm_provider,
        started_at=timezone.now() if status == Run.Status.RUNNING else None,
    )


def append_event(
    run: Run | int,
    *,
    seq: int,
    kind: str,
    payload: dict | None = None,
) -> RunEvent:
    """Add one ordered log line to a run (checks, tools, errors, etc.)."""
    if isinstance(run, int):
        run = Run.objects.get(pk=run)
    return RunEvent.objects.create(run=run, seq=seq, kind=kind, payload=payload or {})


def finish_run(
    run: Run | int,
    *,
    status: str,
    output: dict | None = None,
    flags: dict | None = None,
    tool_call_count: int | None = None,
    elapsed_seconds: float | None = None,
    finished_at: datetime | None = None,
) -> Run:
    """Mark a run complete (or failed/partial) and store its final output."""
    if isinstance(run, int):
        run = Run.objects.get(pk=run)
    run.status = status
    run.finished_at = finished_at or timezone.now()
    if output is not None:
        run.output = output
    if flags is not None:
        run.flags = flags
    if tool_call_count is not None:
        run.tool_call_count = tool_call_count
    if elapsed_seconds is not None:
        run.elapsed_seconds = elapsed_seconds
    run.save(
        update_fields=[
            "status",
            "finished_at",
            "output",
            "flags",
            "tool_call_count",
            "elapsed_seconds",
        ]
    )
    return run


def get_run_with_events(run_id: int) -> Run:
    """Load a run and prefetch its events in order for API responses."""
    return Run.objects.prefetch_related("events").get(pk=run_id)


def get_session(session_id: UUID) -> Session:
    """Fetch one session by UUID for API routes."""
    return Session.objects.get(pk=session_id)


def update_session_profile(session: Session | UUID, profile: dict) -> Session:
    """Replace the intake profile JSON (PUT /profile); does not start a run."""
    if isinstance(session, UUID):
        session = Session.objects.get(pk=session)
    session.profile = profile
    session.save(update_fields=["profile"])
    return session


# Async-friendly aliases for FastAPI route handlers and async tests.
create_session_async = sync_to_async(create_session)
add_document_async = sync_to_async(add_document)
add_message_async = sync_to_async(add_message)
create_run_async = sync_to_async(create_run)
append_event_async = sync_to_async(append_event)
finish_run_async = sync_to_async(finish_run)
get_run_with_events_async = sync_to_async(get_run_with_events)
get_session_async = sync_to_async(get_session)
update_session_profile_async = sync_to_async(update_session_profile)
