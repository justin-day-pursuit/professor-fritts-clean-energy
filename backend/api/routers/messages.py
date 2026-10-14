"""
Chat messages API — user message triggers one harness run.
"""

from __future__ import annotations

from uuid import UUID

from asgiref.sync import sync_to_async
from fastapi import APIRouter, HTTPException

from agent.harness import run_harness
from api import schemas
from core import services
from core.models import Run

router = APIRouter(prefix="/sessions", tags=["messages"])


@router.post("/{session_id}/messages", response_model=schemas.MessageRunResponse)
async def post_message(session_id: UUID, body: schemas.MessageCreateRequest):
    """Append the user message, run the harness, return assistant message and run."""
    try:
        session = await services.get_session_async(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    await services.add_message_async(session_id, role="user", content=body.content)

    run = await sync_to_async(run_harness)(session, body.content, llm_provider=body.llm_provider)

    def _assistant_for_run(run_id: int):
        from core.models import Message

        return Message.objects.filter(run_id=run_id, role="assistant").order_by("-id").first()

    assistant_msg = await sync_to_async(_assistant_for_run)(run.pk)

    run_loaded = await services.get_run_with_events_async(run.pk)
    return schemas.MessageRunResponse(
        message=schemas.MessageResponse.model_validate(assistant_msg) if assistant_msg else None,
        run=schemas.run_to_response(run_loaded),
    )
