"""
Dev routes for the local landing page — list mock situations and run one.

These routes do not accept an LLM provider. The server LLM_PROVIDER decides
whether the run calls Claude or replays the scripted transcript. Tools stay
on TOOL_MODE (mock in v0).
"""

from __future__ import annotations

from asgiref.sync import sync_to_async
from django.conf import settings
from fastapi import APIRouter, HTTPException

from agent.harness import run_harness
from api import schemas
from core import services
from mocks.catalog import list_fixtures, load_case

router = APIRouter(prefix="/dev", tags=["dev"])


def _server_llm_provider() -> str | None:
    """Same rule as the chat route: the browser cannot pick anthropic on its own."""
    return getattr(settings, "LLM_PROVIDER", "anthropic")


@router.get("/fixtures", response_model=schemas.FixtureListResponse)
def get_fixtures() -> schemas.FixtureListResponse:
    """List every fixture folder that has an intake file."""
    return schemas.FixtureListResponse(
        fixtures=[schemas.FixtureSummary(**item) for item in list_fixtures()]
    )


class MissingFixture(Exception):
    """Raised in the sync worker so the async route can turn it into HTTP 404."""


def _run_case(case: str):
    """
    Create a session from the fixture intake and run the harness once.

    Called through sync_to_async because it uses the Django ORM and the harness.
    """
    try:
        profile, question = load_case(case)
    except FileNotFoundError as exc:
        raise MissingFixture(case) from exc
    session = services.create_session(profile=profile, fixture_case=case)
    services.add_message(session, role="user", content=question)
    run = run_harness(session, question, llm_provider=_server_llm_provider())
    loaded = services.get_run_with_events(run.pk)
    return schemas.FixtureRunResponse(run=schemas.run_to_response(loaded))


@router.post("/fixtures/{case}/run", response_model=schemas.FixtureRunResponse)
async def run_fixture(case: str) -> schemas.FixtureRunResponse:
    """
    Run one mock situation and return the full event trace.

    A failed or partial model still returns 200 so the page can show that
    thinking ended. Unknown folder names return 404.
    """
    try:
        return await sync_to_async(_run_case)(case)
    except MissingFixture as exc:
        raise HTTPException(status_code=404, detail=f"No fixture named {exc}") from exc
