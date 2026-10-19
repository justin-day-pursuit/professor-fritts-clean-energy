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


def _model_id() -> str:
    import os

    return os.environ.get("ANTHROPIC_MODEL", "").strip() or "claude-sonnet-5-5"


@router.post("/chat", response_model=schemas.PlanChatResponse)
def plan_chat(request: schemas.PlanChatRequest) -> schemas.PlanChatResponse:
    """
    Chat and brainstorm with Claude in the context of the generated clean energy plan.
    """
    import json
    import os

    summary = request.plan_summary
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            system = (
                "You are Professor Fritts, a warm, knowledgeable, practical clean energy engineer and guide for NYC public buildings. "
                "The visitor has just viewed the clean energy plan below and wants to brainstorm, ask follow-up questions, understand trade-offs, "
                "or consider adjustments.\n\n"
                "Rules:\n"
                "- Speak directly as Professor Fritts in a warm, encouraging, conversational tone suited for reading in your speech bubble.\n"
                "- Keep answers clear, direct, and concise (1-2 short paragraphs, under 160 words).\n"
                "- Reference the specific numbers, costs, solar estimates, battery sizing, or building facts from the plan.\n"
                "- If asked about missing info or next steps, explain what engineer or city reviews are needed.\n"
                "- Conclude with a helpful thought or question to keep the brainstorming going.\n\n"
                f"Clean Energy Plan Context:\n{json.dumps(summary, indent=2)}"
            )
            messages = [{"role": h.role, "content": h.content} for h in request.history if h.role in ("user", "assistant")]
            messages.append({"role": "user", "content": question})
            response = client.messages.create(
                model=_model_id(),
                max_tokens=600,
                system=system,
                messages=messages,
            )
            text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
            if text.strip():
                return schemas.PlanChatResponse(reply=text.strip())
        except Exception:
            logger.exception("Live Claude call failed for plan chat, using fallback response")

    building_name = summary.get("building", {}).get("intake", {}).get("building_name") or "your building"
    q_lower = question.lower()

    if "missing" in q_lower or "next step" in q_lower or "actionable" in q_lower:
        referrals = summary.get("referrals", [])
        ref_text = "; ".join(r.get("text", "") for r in referrals[:3]) if referrals else "structural review and utility interconnection approval"
        reply = (
            f"To take the plan for {building_name} to the next stage, the primary items needed are: {ref_text}. "
            "Having an engineer or licensed professional verify usable roof area and electrical capacity is typically the highest priority next step."
        )
    elif "cost" in q_lower or "budget" in q_lower or "reduce" in q_lower or "upfront" in q_lower or "payback" in q_lower:
        scenarios = summary.get("scenarios", {})
        scen_names = [s.get("title", f"Scenario {k}") for k, s in scenarios.items() if isinstance(s, dict)]
        reply = (
            f"For {building_name}, we evaluated several approaches ({', '.join(scen_names) if scen_names else 'Scenarios A, B, and C'}). "
            "To reduce upfront capital expenditure, you can phase the project by starting with efficiency measures (Scenario A) or exploring NYSERDA and utility incentives to offset equipment costs before adding battery storage."
        )
    elif "explain" in q_lower or "section" in q_lower:
        sections = summary.get("sections", [])
        matched = next((s for s in sections if any(w in s.get("title", "").lower() for w in q_lower.split())), None)
        if matched and matched.get("claims"):
            detail = " ".join(c.get("text", "") for c in matched["claims"][:2])
            reply = f"Here is the key takeaway for '{matched.get('title')}': {detail}"
        else:
            outcome = summary.get("outcome", {}).get("label") or "your clean energy analysis"
            reply = f"Here is what our analysis found for {building_name}: {outcome}. You can ask me to break down any specific section or scenario in detail!"
    else:
        outcome = summary.get("outcome", {}).get("label") or "We've mapped out renewable options"
        reply = (
            f"Looking at {building_name}: {outcome}. "
            "We can adjust the battery sizing, change the target year, or prioritize efficiency versus solar. What would you like to explore next?"
        )

    return schemas.PlanChatResponse(reply=reply)
