"""
Pydantic models that describe API JSON — mirrors of core database rows for responses.

Unit 3 will extend these when session and run routes are added.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Body returned by GET /api/health — process is up and env modes are visible."""

    status: str
    tool_mode: str
    llm_provider: str
    django_version: str


class SessionCreateRequest(BaseModel):
    """Optional initial profile and mock fixture case name."""

    profile: dict[str, Any] = Field(default_factory=dict)
    fixture_case: str | None = None


class ProfileUpdateRequest(BaseModel):
    """Full intake profile replacement from the frontend form."""

    profile: dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """One planning session as the API will return it."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    profile: dict[str, Any] = Field(default_factory=dict)
    status: str
    fixture_case: str = "case1_queens_library"


class DocumentResponse(BaseModel):
    """Uploaded file metadata for a session."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    stored_path: str
    parsed_summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MessageResponse(BaseModel):
    """Chat message in a session."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: UUID
    role: str
    content: str
    created_at: datetime
    run_id: int | None = None


class RunEventResponse(BaseModel):
    """Single step in a run log."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    seq: int
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MessageCreateRequest(BaseModel):
    """User chat line — LLM mode comes from server LLM_PROVIDER, not the request body."""

    content: str


class MessageRunResponse(BaseModel):
    message: MessageResponse | None = None
    run: "RunResponse"


class FixtureSummary(BaseModel):
    """One mock situation the dev landing page can start."""

    id: str
    building_name: str
    goal: str
    question: str


class FixtureListResponse(BaseModel):
    """Body of GET /api/dev/fixtures."""

    fixtures: list[FixtureSummary]


class FixtureRunResponse(BaseModel):
    """Body of POST /api/dev/fixtures/{case}/run — the finished trace, even on failure."""

    run: "RunResponse"


class RunResponse(BaseModel):
    """Agent run with optional ordered events."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: UUID
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    tool_mode: str
    llm_provider: str
    tool_call_count: int
    elapsed_seconds: float | None
    output: dict[str, Any] = Field(default_factory=dict)
    flags: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    events: list[RunEventResponse] = Field(default_factory=list)


def run_to_response(run) -> RunResponse:
    """Build RunResponse from a Run with prefetched events."""
    events = [
        RunEventResponse(
            id=e.id,
            seq=e.seq,
            kind=e.kind,
            payload=e.payload,
            created_at=e.created_at,
        )
        for e in run.events.all()
    ]
    return RunResponse(
        id=run.id,
        session_id=run.session_id,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        tool_mode=run.tool_mode,
        llm_provider=run.llm_provider,
        tool_call_count=run.tool_call_count,
        elapsed_seconds=run.elapsed_seconds,
        output=run.output,
        flags=run.flags,
        created_at=run.created_at,
        events=events,
    )


class RoofBuilding(BaseModel):
    """One building outline on the tax lot, with the ground area that was measured from it."""

    area_sqft: int
    height_ft: float | None = None
    construction_year: int | None = None
    name: str | None = None
    counted: bool


class RoofSuggestionResponse(BaseModel):
    """A suggested roof area from city building footprints, with its source and what it is not."""

    suggested_roof_area_sqft: int
    total_footprint_sqft: int
    largest_footprint_sqft: int
    building_count: int
    buildings: list[RoofBuilding]
    bbl: str
    geocoder_match: str | None = None
    source_url: str
    retrieved_at: str
    note: str


class PrefillItem(BaseModel):
    """One value the city's records suggest for the form, with where it came from and what to keep in mind."""

    field: str
    label: str
    # The number, text or yes/no the form should show.
    value: float | int | str | bool
    # The same value written for a person to read.
    display: str
    source: str
    source_url: str
    note: str


class BuildingPrefillResponse(BaseModel):
    """What the city already knows about one tax lot, as form values, plus a sentence for each part it could not find."""

    bbl: str
    items: list[PrefillItem]
    missing: list[str]


class ReplayCase(BaseModel):
    """One saved demo the planner can replay: what it is, and whether it is a recording or a script."""

    id: str
    label: str
    tag: str
    # "recorded" = a real Claude run saved as it happened; "scripted" = text written by us from real tool numbers.
    kind: str
    question: str


class ReplayCaseListResponse(BaseModel):
    """GET /api/replay/cases."""

    cases: list[ReplayCase]


class ReplayResponse(BaseModel):
    """A replayed run: the session it used, the plan message, and the full run with its events."""

    session: SessionResponse
    message: MessageResponse | None = None
    run: "RunResponse"
    case: ReplayCase


class PlanPdfRequest(BaseModel):
    """POST /api/plans/pdf: the plan summary (output.plan_summary) to turn into a PDF."""

    plan_summary: dict[str, Any]
