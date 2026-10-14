"""
Session API — create and read planning sessions, update intake profile.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from api import schemas
from core import services

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=schemas.SessionResponse)
async def create_session(body: schemas.SessionCreateRequest):
    """Start a session; optional fixture_case selects mock data folder."""
    session = await services.create_session_async(
        profile=body.profile,
        fixture_case=body.fixture_case or "case1_queens_library",
    )
    return schemas.SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=schemas.SessionResponse)
async def get_session(session_id: UUID):
    """Return one session including its profile JSON."""
    try:
        session = await services.get_session_async(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return schemas.SessionResponse.model_validate(session)


@router.put("/{session_id}/profile", response_model=schemas.SessionResponse)
async def put_profile(session_id: UUID, body: schemas.ProfileUpdateRequest):
    """Save intake form fields to session.profile; does not run the agent."""
    try:
        session = await services.update_session_profile_async(session_id, body.profile)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return schemas.SessionResponse.model_validate(session)
