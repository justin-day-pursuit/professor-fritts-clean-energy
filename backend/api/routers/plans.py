"""
Plan downloads.

POST /api/plans/pdf takes a plan summary (the same JSON the agent writes as output.plan_summary) and returns the plan as a PDF
file. It reads only what it is sent, makes no outside calls and uses no Claude credits, so it works in any TOOL_MODE and for
any saved run. The PDF carries the plain report only, never the developer view.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Response

from agent.plan_pdf import build_plan_pdf, pdf_filename
from api import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/pdf")
def plan_pdf(request: schemas.PlanPdfRequest) -> Response:
    """
    Make a PDF of one plan.

    A plain `def` on purpose: drawing the PDF is CPU work, and FastAPI runs it in a worker thread so it does not block other
    requests.
    """
    summary = request.plan_summary
    if not summary.get("outcome") and not summary.get("sections"):
        raise HTTPException(status_code=422, detail="That is not a plan summary: it has no short answer and no report sections.")
    try:
        pdf = build_plan_pdf(summary)
    except Exception as exc:  # noqa: BLE001 - any drawing failure becomes one plain message
        logger.exception("Could not build the plan PDF")
        raise HTTPException(status_code=500, detail="The PDF could not be made from this plan.") from exc
    filename = pdf_filename(summary)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            # Lets the page read the file name from a browser request to another address.
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
