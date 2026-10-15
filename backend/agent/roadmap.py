"""
Render the structured roadmap payload to Markdown and JSON for download and UI.

From v2 the plan always has the 13 PRD sections in order. A section the model left out still
prints, with a plain "not provided" line, so a reader can see what is missing instead of
wondering. Section 3 is built from the assumptions register (A1, A2, ...).
"""

from __future__ import annotations

import re

from agent.claims import SECTION_TITLES, Claim, RoadmapPayload, RoadmapSection

# What a reader sees when the model gave nothing for a section.
MISSING_SECTION_TEXT = "Not provided in this run."

# The register section, named once so the code below does not repeat a magic string.
ASSUMPTIONS_SECTION_ID = "3"


def _format_range(claim: Claim) -> str:
    """
    Turn a claim's low/high/units into text like '55,000–66,000 kWh/yr'.

    Returns an empty string when the claim has no numbers, so word-only claims print as before.
    """
    if claim.value_low is None or claim.value_high is None:
        return ""
    low, high = claim.value_low, claim.value_high
    # Show whole numbers without decimals, and keep decimals for small values like $/kWh.
    def fmt(value: float) -> str:
        return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.4g}"

    units = claim.units or ""
    if low == high:
        return f"{fmt(low)} {units}".strip()
    return f"{fmt(low)}–{fmt(high)} {units}".strip()


def _format_claim(claim: Claim, *, section_id: str = "") -> str:
    """
    One bullet with label, confidence, number range and traceability for download and UI.

    Assumptions show their register id (A1, A2, ...); other claims show their source or calculation.
    """
    value_text = _format_range(claim)
    value_part = f" [{value_text}]" if value_text else ""
    if claim.label == "ASSUMPTION" and claim.assumption_id:
        extra = ""
        if claim.source_url or claim.calc_id:
            opt = claim.calc_id or claim.source_url
            extra = f" — optional source/calc: `{opt}`"
        return (
            f"- **{claim.label}** ({claim.confidence}) [{claim.assumption_id}]: {claim.text}"
            f"{value_part}{extra}"
        )
    trace = claim.calc_id or claim.source_url or "n/a"
    _ = section_id  # reserved for section-specific layout later
    return (
        f"- **{claim.label}** ({claim.confidence}): {claim.text}{value_part} "
        f"— source/calc: `{trace}`"
    )


def _assumption_sort_key(assumption_id: str) -> tuple[int, str]:
    """Sort A2 before A10 by the number inside the id; ids with no number go last."""
    match = re.search(r"\d+", assumption_id)
    return (int(match.group()) if match else 10**9, assumption_id)


def build_assumptions_register(payload: RoadmapPayload) -> list[Claim]:
    """
    Collect every ASSUMPTION claim in the plan, once per id, sorted A1, A2, A3 ...

    The register is the single list of what the plan guessed. If the model wrote the same id in
    two places, the first one wins so the list never shows the same assumption twice.
    """
    by_id: dict[str, Claim] = {}
    for section in payload.sections:
        for claim in section.claims:
            if claim.label == "ASSUMPTION" and claim.assumption_id:
                by_id.setdefault(claim.assumption_id, claim)
    return [by_id[key] for key in sorted(by_id, key=_assumption_sort_key)]


def ordered_sections(payload: RoadmapPayload) -> list[RoadmapSection]:
    """
    Return the 13 PRD sections in order, filling gaps with empty placeholders.

    Sections with ids outside 1-13 (for example 'follow_up' in chat answers) are kept after
    the numbered ones, so nothing the model wrote is dropped.
    """
    given = {section.section_id: section for section in payload.sections}
    result: list[RoadmapSection] = []
    for section_id, title in SECTION_TITLES.items():
        section = given.pop(section_id, None)
        if section is None:
            section = RoadmapSection(section_id=section_id, title=title, claims=[])
        else:
            # Always print the PRD's title, whatever wording the model chose, so every plan
            # reads the same and the headings can be checked by a script.
            section = section.model_copy(update={"title": title})
        result.append(section)
    result.extend(given.values())
    return result


def render_roadmap_markdown(payload: RoadmapPayload) -> str:
    """
    Build human-readable Markdown with the 13 section headers and labeled claims.

    Edit heading text in agent.claims.SECTION_TITLES when the product PRD section titles change.
    """
    lines = ["# Professor Fritts — Priority roadmap", ""]
    register = build_assumptions_register(payload)
    for section in ordered_sections(payload):
        lines.append(f"## {section.section_id}. {section.title}")
        if section.stand_in_note:
            lines.append(f"*{section.stand_in_note}*")
        lines.append("")
        if section.section_id == ASSUMPTIONS_SECTION_ID and register:
            # Section 3 is the register: every assumption in the plan, in id order.
            claims = register
        else:
            claims = section.claims
        if not claims:
            lines.append(f"*{MISSING_SECTION_TEXT}*")
        for claim in claims:
            lines.append(_format_claim(claim, section_id=section.section_id))
        lines.append("")

    if payload.footer_note:
        lines.append("---")
        lines.append(f"*{payload.footer_note}*")
    return "\n".join(lines).rstrip() + "\n"


def render_roadmap_json(payload: RoadmapPayload) -> dict:
    """JSON-serializable dict mirroring the structured payload plus rendered markdown."""
    return {
        "roadmap": payload.model_dump(),
        "markdown": render_roadmap_markdown(payload),
    }


def render_follow_up_markdown(summary: str, payload: RoadmapPayload) -> str:
    """
    Build chat Markdown for write_answer: lead with the summary, then the labeled claims.

    A follow-up is a short answer, not a full plan, so it lists only the sections it has
    instead of printing 13 "not provided" placeholders.
    """
    lines: list[str] = []
    for section in payload.sections:
        if not section.claims:
            continue
        lines.append(f"### {section.title}")
        for claim in section.claims:
            lines.append(_format_claim(claim, section_id=section.section_id))
        lines.append("")
    body = "\n".join(lines).strip()
    return f"{summary.strip()}\n\n{body}".strip()
