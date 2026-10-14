"""
Run log and roadmap download routes.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response

from api import schemas
from core import services

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}", response_model=schemas.RunResponse)
async def get_run(run_id: int):
    """Return run metadata and ordered events."""
    try:
        run = await services.get_run_with_events_async(run_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return schemas.run_to_response(run)


@router.get("/{run_id}/roadmap.md")
async def get_roadmap_md(run_id: int):
    """Download rendered roadmap Markdown."""
    try:
        run = await services.get_run_with_events_async(run_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    md = (run.output or {}).get("markdown") or ""
    if not md:
        raise HTTPException(status_code=404, detail="No roadmap on this run")
    return PlainTextResponse(md, media_type="text/markdown")


@router.get("/{run_id}/roadmap.json")
async def get_roadmap_json(run_id: int):
    """Download structured roadmap JSON."""
    try:
        run = await services.get_run_with_events_async(run_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    payload = (run.output or {}).get("roadmap")
    if not payload:
        raise HTTPException(status_code=404, detail="No roadmap on this run")
    return Response(content=json.dumps(payload, indent=2), media_type="application/json")
