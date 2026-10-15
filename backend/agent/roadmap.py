"""
Render the structured roadmap payload to Markdown and JSON for download and UI.

Section numbers follow the product PRD so v2 can fill in 4, 7, and 11 later.
"""

from __future__ import annotations

from agent.claims import Claim, RoadmapPayload


def _format_claim(claim: Claim, *, section_id: str = "") -> str:
    """
    One bullet with label, confidence, and traceability for download and UI.

    Section 3 lists assumptions by register id; section 8 keeps source/calc for actions.
    """
    if claim.label == "ASSUMPTION" and claim.assumption_id:
        extra = ""
        if claim.source_url or claim.calc_id:
            opt = claim.calc_id or claim.source_url
            extra = f" — optional source/calc: `{opt}`"
        return (
            f"- **{claim.label}** ({claim.confidence}) [{claim.assumption_id}]: {claim.text}"
            f"{extra}"
        )
    trace = claim.calc_id or claim.source_url or "n/a"
    _ = section_id  # reserved for section-specific layout later (sections 3 and 8 in v0)
    return (
        f"- **{claim.label}** ({claim.confidence}): {claim.text} "
        f"— source/calc: `{trace}`"
    )


def render_roadmap_markdown(payload: RoadmapPayload) -> str:
    """
    Build human-readable Markdown with section headers and labeled claims.

    Edit heading text here when the product PRD section titles change.
    """
    lines = ["# Professor Fritts — Priority roadmap (v0 stand-in)", ""]
    for section in payload.sections:
        lines.append(f"## {section.section_id}. {section.title}")
        if section.stand_in_note:
            lines.append(f"*{section.stand_in_note}*")
        lines.append("")
        for claim in section.claims:
            lines.append(_format_claim(claim, section_id=section.section_id))
        lines.append("")

    lines.append("---")
    lines.append(f"*{payload.footer_note}*")
    return "\n".join(lines)


def render_roadmap_json(payload: RoadmapPayload) -> dict:
    """JSON-serializable dict mirroring the structured payload plus rendered markdown."""
    return {
        "roadmap": payload.model_dump(),
        "markdown": render_roadmap_markdown(payload),
    }


def render_follow_up_markdown(summary: str, payload: RoadmapPayload) -> str:
    """
    Build chat Markdown for write_answer: lead with the summary, then labeled claims.

    If the product changes how follow-ups look, edit the summary line and reuse render_roadmap_markdown
    for the claim sections below it.
    """
    body = render_roadmap_markdown(payload)
    # Follow-ups use a shorter header block; strip the default roadmap title for readability.
    if body.startswith("# Professor Fritts"):
        _, _, rest = body.partition("\n\n")
        body = rest if rest else body
    return f"{summary.strip()}\n\n{body}".strip()
