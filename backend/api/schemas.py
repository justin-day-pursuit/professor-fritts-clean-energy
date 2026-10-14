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


class SessionResponse(BaseModel):
    """One planning session as the API will return it."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    profile: dict[str, Any] = Field(default_factory=dict)
    status: str


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
