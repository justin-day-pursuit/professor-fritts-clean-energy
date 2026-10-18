"""
The plan as a PDF a facilities manager can save, print or send to a board.

It is built from the plan summary the agent writes with every run (output.plan_summary), and shows the same plain-language report
the plan page shows: the short answer, what to confirm first, the three plans side by side, what the totals leave out, every
statement with its label and source, who to contact, and the sources. The developer view (calculation ids, flag names, raw tool
data) is never included. The PDF is drawn directly, with no browser involved, so it needs nothing beyond the ReportLab library.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK = colors.HexColor("#12303d")
MUTE = colors.HexColor("#5b6b72")
TEAL = colors.HexColor("#1c8c7e")
GOLD = colors.HexColor("#f5b83d")
WARN = colors.HexColor("#c2562b")
SOFT = colors.HexColor("#f1ecdf")
LINE = colors.HexColor("#e6dfce")

LABEL_COLORS = {
    "FACT": colors.HexColor("#1c8c7e"),
    "ESTIMATE": colors.HexColor("#2f6fb5"),
    "ASSUMPTION": colors.HexColor("#b7791f"),
    "RECOMMENDATION": colors.HexColor("#7a4fb0"),
}

# What each label means, with an example and what to do about it (the same words as the plan page).
LABEL_EXPLAINED = {
    "FACT": ("From a named source.", "The size of the roof, from the city's roof check.", "Trust it. The source is linked so you can look."),
    "ESTIMATE": (
        "Calculated from the building's data, and always shown as a range.",
        "How much grid electricity a plan would cut.",
        "Use it to compare the plans. Expect it to move once an audit and contractor bids are in.",
    ),
    "ASSUMPTION": (
        "A starting point used because the real number isn't known.",
        "The state-average electricity price, or the savings percent for efficiency work.",
        "Check it. You can change it: enter your own electricity price and the plan changes to match. The efficiency savings percent stays a planning estimate until an energy audit.",
    ),
    "RECOMMENDATION": (
        "A suggested next step.",
        "Have a roofer look at the roof before any panels are ordered.",
        "Take it to the professional it names. They make the final call.",
    ),
}

# The section titles as a reader would say them (the plan page uses the same three).
SECTION_NAME = {
    "3": "Assumptions behind the numbers",
    "12": "What is uncertain, and what would help",
    "13": "Sources",
}

# Characters the built-in PDF font cannot draw, swapped for plain ones.
_SWAPS = {"→": "to", "≥": ">=", "≤": "<=", "≈": "about", "−": "-", "‑": "-", " ": " ", " ": " ", " ": " ", "•": "-"}


def plainify(text: str) -> str:
    """
    Cleans a sentence for a reader, the same way the plan page does: removes assumption and calculation ids, flag names and
    "placeholder" wording. (Ported from frontend/app/plan-mockup/plain.ts, so the two stay in step.)
    """
    ident = r"(?:A\d{1,2}|C[1-4]|F-[ABC])"
    idlist = rf"{ident}(?:\s*(?:,|/|and|&)\s*{ident})*"
    out = re.sub(r"^\s*A\d{1,2}\s*[:\-.]\s*", "", text)
    out = re.sub(r"^\s*Flag [a-z0-9_:]+:\s*", "", out, flags=re.I)
    out = re.sub(rf"\s*\(\s*{idlist}\s*\)", "", out)
    out = re.sub(rf",?\s*\bassumptions?\s+{idlist}", "", out, flags=re.I)
    out = re.sub(rf",\s*{ident}(?=\s*\))", "", out)
    out = re.sub(rf"\b(?:the|this|that)\s+{ident}\s+", lambda m: m.group(0).split()[0] + " ", out, flags=re.I)
    out = re.sub(rf"\b(?:see|and|in|from|on)\s+{idlist}\b", "", out, flags=re.I)
    out = re.sub(rf"\s+{ident}\b", "", out)
    out = re.sub(r"(?<![/\-\w])(?<!\w\.)[a-z]{2,}(?:_[a-z0-9]+)+(?![/\-\w])(?!\.\w)", lambda m: m.group(0).replace("_", " "), out)
    out = re.sub(r"\bteam planning (?:placeholder|figure)s?\b", "planning estimate", out, flags=re.I)
    out = re.sub(r"\bteam placeholders?\b", lambda m: "planning estimates" if m.group(0).lower().endswith("s") else "planning estimate", out, flags=re.I)
    out = re.sub(r"\bplaceholders\b", "planning estimates", out, flags=re.I)
    out = re.sub(r"\bplaceholder\b", "planning estimate", out, flags=re.I)
    out = re.sub(r"25th\s*(?:-|to)\s*75th percentile", "middle half", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([.,;:])", r"\1", out)
    out = re.sub(r",\s*([;.])", r"\1", out)
    return out.strip()


def safe(text: Any) -> str:
    """Text made safe to draw: unsupported characters swapped, then escaped for the PDF's tiny markup language."""
    value = "" if text is None else str(text)
    for old, new in _SWAPS.items():
        value = value.replace(old, new)
    value = value.encode("cp1252", "ignore").decode("cp1252")
    return escape(value)


def money(value: float | int | None) -> str:
    """A dollar amount in short form: $592k, $1.08M."""
    if value is None:
        return "n/a"
    v = float(value)
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.2f}M".replace(".00M", "M")
    if abs(v) >= 10_000:
        return f"${round(v / 1000):,}k"
    return f"${round(v):,}"


def money_range(pair: Any) -> str:
    """A low-to-high dollar range."""
    if not pair or len(pair) != 2:
        return "n/a"
    low, high = pair
    return money(low) if round(low) == round(high) else f"{money(low)} to {money(high)}"


def number_range(pair: Any, unit: str = "", digits: int = 0) -> str:
    """A low-to-high number range with an optional unit, like '9 to 30 years'."""
    if not pair or len(pair) != 2:
        return "n/a"
    low, high = (round(float(x), digits) for x in pair)
    fmt = (lambda x: f"{x:,.{digits}f}")
    body = fmt(low) if low == high else f"{fmt(low)} to {fmt(high)}"
    return f"{body}{unit}"


def split_headline(text: str) -> tuple[str, str]:
    """A statement's first sentence (the headline) and the rest (the reasoning)."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z$(])", text, maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK, alignment=TA_LEFT)
    return {
        "body": base,
        "small": ParagraphStyle("small", parent=base, fontSize=8, leading=10.5, textColor=MUTE),
        "mute": ParagraphStyle("mute", parent=base, textColor=MUTE),
        "brand": ParagraphStyle("brand", parent=base, fontName="Helvetica-Bold", fontSize=8.5, textColor=TEAL, spaceAfter=2),
        "title": ParagraphStyle("title", parent=base, fontName="Helvetica-Bold", fontSize=22, leading=26, spaceAfter=4),
        "headline": ParagraphStyle("headline", parent=base, fontName="Helvetica-Bold", fontSize=17, leading=21, spaceAfter=6),
        "h1": ParagraphStyle("h1", parent=base, fontName="Helvetica-Bold", fontSize=14, leading=18, spaceBefore=14, spaceAfter=6, keepWithNext=1),
        "h2": ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4, keepWithNext=1),
        "bold": ParagraphStyle("bold", parent=base, fontName="Helvetica-Bold"),
        "cell": ParagraphStyle("cell", parent=base, fontSize=8.5, leading=11),
        "cellhead": ParagraphStyle("cellhead", parent=base, fontName="Helvetica-Bold", fontSize=8.5, leading=11),
        "bullet": ParagraphStyle("bullet", parent=base, leftIndent=12, bulletIndent=0, spaceAfter=3),
    }


def _link(url: str | None, text: str = "source") -> str:
    """A clickable link, or nothing when there is no address."""
    if not url:
        return ""
    return f'<a href="{safe(url)}" color="#1c8c7e">{safe(text)}</a>'


def _claim(claim: dict[str, Any], st: dict[str, ParagraphStyle]) -> KeepTogether:
    """One statement: a bold headline, the reasoning under it, then its label, confidence and source on one quiet line."""
    headline, reasoning = split_headline(plainify(str(claim.get("text", ""))))
    label = str(claim.get("label", "")).upper()
    color = LABEL_COLORS.get(label, MUTE).hexval()[2:]
    meta = [f'<font color="#{color}"><b>{safe(label.title())}</b></font>']
    if claim.get("confidence"):
        meta.append(f"{safe(claim['confidence'])} confidence")
    if claim.get("source_url"):
        meta.append(_link(claim["source_url"]))
    items = [Paragraph(f"<b>{safe(headline)}</b>", st["body"])]
    if reasoning:
        items.append(Paragraph(safe(reasoning), st["mute"]))
    items.append(Paragraph(" &nbsp;|&nbsp; ".join(meta), st["small"]))
    items.append(Spacer(1, 7))
    return KeepTogether(items)


def _scenario_table(summary: dict[str, Any], st: dict[str, ParagraphStyle], width: float) -> Table:
    """The three plans as columns and the questions a reader asks as rows."""
    by_id = {s.get("scenario_id"): s for s in summary.get("scenarios", [])}
    recommended = (summary.get("outcome") or {}).get("recommended")
    names = {"A": "Plan A", "B": "Plan B", "C": "Plan C"}
    packages = {"A": "Efficiency only", "B": "Efficiency and solar", "C": "Full path"}

    def package_text(s: dict[str, Any]) -> str:
        pkg = s.get("package") or {}
        parts = ["Expanded efficiency" if pkg.get("efficiency_level") == "deep" else "Standard efficiency"]
        if pkg.get("solar_kw_dc"):
            parts.append(f"solar ({pkg['solar_kw_dc']} kW)")
        if pkg.get("battery_kwh"):
            parts.append(f"{pkg['battery_kwh']} kWh battery")
        return " + ".join(parts)

    def cell(fn) -> list[Paragraph]:
        row = []
        for pid in ("A", "B", "C"):
            s = by_id.get(pid)
            row.append(Paragraph(safe(fn(s)) if s else "Not costed in this plan.", st["cell"]))
        return row

    def goal_text(s: dict[str, Any]) -> str:
        goal = s.get("goal_pct") or 30
        return f"Reaches your {goal:g}% goal even at the low end." if s.get("reaches_goal") else f"Does not reach {goal:g}% at the low end."

    def credit_text(s: dict[str, Any]) -> str:
        credit = s.get("incentives_counted_usd") or [0, 0]
        if credit[1] > 0:
            return f"{money_range(s.get('net_cost_usd'))} after a {money_range(credit)} federal credit"
        return "No incentive counted"

    head = [Paragraph("", st["cellhead"])]
    for pid in ("A", "B", "C"):
        tag = " (recommended)" if recommended == pid else ""
        s = by_id.get(pid)
        shade = "#12303d" if recommended == pid else "#5b6b72"
        sub = f"<br/><font size=7.5 color='{shade}'>{safe(package_text(s) if s else packages[pid])}</font>"
        head.append(Paragraph(f"<b>{names[pid]}{tag}</b>{sub}", st["cellhead"]))

    rows: list[list[Any]] = [head]
    spec = [
        ("Cuts grid electricity", lambda s: f"{number_range(s.get('reduction_pct_of_use'), '%')} of use. {goal_text(s)}"),
        ("Upfront cost", lambda s: f"Typical range {money_range(s.get('upfront_usd'))}" + (f". Median of similar NYC projects: about {money(s['upfront_usd_best'])}." if s.get("upfront_usd_best") else "")),
        ("After incentives", credit_text),
        ("Saves each year", lambda s: money_range(s.get("annual_savings_usd"))),
        ("Pays back in", lambda s: number_range(s.get("payback_years"), " years") + (f" (about {round(s['payback_years_best'])} at the median cost)" if s.get("payback_years_best") else "")),
        ("Backup power", lambda s: number_range(s.get("outage_hours"), " hours")),
        ("Against your budget", lambda s: plainify(str(s.get("budget_note") or s.get("budget_strain") or "")).strip() or "n/a"),
    ]
    for label, fn in spec:
        rows.append([Paragraph(f"<b>{safe(label)}</b>", st["cell"]), *cell(fn)])

    first = 1.25 * inch
    rest = (width - first) / 3
    table = Table(rows, colWidths=[first, rest, rest, rest], repeatRows=1)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), SOFT),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for col, pid in enumerate(("A", "B", "C"), start=1):
        if recommended == pid:
            style.append(("BACKGROUND", (col, 0), (col, 0), GOLD))
    table.setStyle(TableStyle(style))
    return table


def _footer(canvas, doc) -> None:  # noqa: ANN001 - ReportLab's callback signature
    """The line at the bottom of every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTE)
    canvas.drawString(0.75 * inch, 0.5 * inch, "Professor Fritts. Planning-level estimates, not quotes. Every plan names the professionals who must review it before any money is committed.")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()


def pdf_filename(summary: dict[str, Any]) -> str:
    """A file name like 'professor-fritts-plan-p-s-236-langston-hughes.pdf'."""
    intake = (summary.get("building") or {}).get("intake") or {}
    name = str(intake.get("building_name") or intake.get("address") or "building")
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "building"
    return f"professor-fritts-plan-{slug}.pdf"


def build_plan_pdf(summary: dict[str, Any], generated_on: date | None = None) -> bytes:
    """The plan summary as the bytes of a PDF file."""
    from io import BytesIO

    st = _styles()
    width = letter[0] - 1.5 * inch
    intake = (summary.get("building") or {}).get("intake") or {}
    outcome = summary.get("outcome") or {}
    story: list[Any] = []

    # ---- the short answer
    story.append(Paragraph("PROFESSOR FRITTS  |  RENEWABLE ENERGY PLANNING FOR NYC PUBLIC BUILDINGS", st["brand"]))
    story.append(Paragraph(safe(intake.get("building_name") or intake.get("address") or "Building plan"), st["title"]))
    address = ", ".join(str(x) for x in (intake.get("address"), intake.get("borough")) if x)
    stamp = (generated_on or date.today()).strftime("%B %d, %Y").replace(" 0", " ")
    story.append(Paragraph(safe(f"{address}  |  Prepared {stamp}" if address else f"Prepared {stamp}"), st["mute"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=8))
    if outcome.get("label"):
        story.append(Paragraph(safe(f"THE SHORT ANSWER  |  {str(outcome['label']).upper()}"), st["brand"]))
    story.append(Paragraph(safe(outcome.get("headline", "")), st["headline"]))
    story.append(Paragraph(safe(plainify(str(outcome.get("subhead", "")))), st["body"]))

    confirm = summary.get("confirm_first") or []
    if confirm:
        story.append(Paragraph("Please confirm first", st["h2"]))
        for item in confirm:
            story.append(Paragraph(safe(plainify(str(item.get("text", "")))), st["bullet"], bulletText="-"))

    # ---- how to read it
    story.append(Paragraph("How to read this plan: what to trust, what to check, and what to hand to a professional", st["h1"]))
    legend = []
    for label, (meaning, example, action) in LABEL_EXPLAINED.items():
        color = LABEL_COLORS[label].hexval()[2:]
        legend.append(
            [
                Paragraph(f'<font color="#{color}"><b>{label.title()}</b></font>', st["cell"]),
                Paragraph(f"<b>{safe(meaning)}</b><br/>For example: {safe(example)}<br/>What to do: {safe(action)}", st["cell"]),
            ]
        )
    legend_table = Table(legend, colWidths=[1.1 * inch, width - 1.1 * inch])
    legend_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(legend_table)
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Costs and savings are shown as ranges because this is an early estimate made from public data, before anyone has walked the building. "
            "A range of about half to double the figure is normal at this stage. An energy audit and contractor bids are what narrow it.",
            st["small"],
        )
    )

    # ---- the three plans
    story.append(Paragraph("Three ways to get there", st["h1"]))
    story.append(_scenario_table(summary, st, width))

    left_out = summary.get("not_included") or []
    if left_out:
        story.append(Paragraph("What the totals leave out", st["h2"]))
        for item in left_out:
            lines = [f"<b>{safe(item.get('item', ''))}.</b> {safe(plainify(str(item.get('why', ''))))} {safe(item.get('next', ''))}"]
            if item.get("rough_guide_usd"):
                lines.append(f"Rough guide: {safe(money_range(item['rough_guide_usd']))}. This is never added to the plan totals.")
            if item.get("basis"):
                lines.append(safe(plainify(str(item["basis"]))))
            story.append(Paragraph("<br/>".join(lines), st["body"]))
            for src in item.get("sources") or []:
                story.append(Paragraph(f"{_link(src.get('url'), 'Source')}: {safe(src.get('label', ''))}", st["small"]))
            story.append(Spacer(1, 4))

    # ---- incentives
    incentives = summary.get("incentives") or []
    if incentives:
        story.append(Paragraph("Incentives that may apply", st["h1"]))
        story.append(Paragraph("Each was re-read from its official page when this plan was made. A program that could not be confirmed is left out of the costs.", st["mute"]))
        story.append(Spacer(1, 4))
        for program in incentives:
            status = str(program.get("status", "")).replace("_", " ").capitalize()
            bits = [f"<b>{safe(program.get('name', ''))}</b>", f"Status: {safe(status)}"]
            if program.get("deadline"):
                bits.append(f"Deadline: {safe(program['deadline'])}")
            if program.get("status_note"):
                bits.append(safe(plainify(str(program["status_note"]))))
            if program.get("source_url"):
                bits.append(_link(program["source_url"], "Official page"))
            story.append(KeepTogether([Paragraph("<br/>".join(bits), st["body"]), Spacer(1, 6)]))

    # ---- the written report, section by section
    story.append(Paragraph("The full report", st["h1"]))
    for section in summary.get("sections") or []:
        sid = str(section.get("section_id", ""))
        claims = section.get("claims") or []
        if sid == "13" and not claims:
            continue
        title = f"{sid}. {SECTION_NAME.get(sid) or plainify(str(section.get('title', '')))}"
        block: list[Any] = [Paragraph(safe(title), st["h2"])]
        if section.get("stand_in_note"):
            block.append(Paragraph(safe(plainify(str(section["stand_in_note"]))), st["small"]))
        story.extend(block)  # the heading stays with the first statement under it
        for claim in claims:
            story.append(_claim(claim, st))

    # ---- who to contact
    referrals = summary.get("referrals") or []
    next_steps = summary.get("next_steps") or []
    if referrals or next_steps:
        story.append(Paragraph("Who to contact", st["h1"]))
        for claim in referrals:
            story.append(_claim(claim, st))
        for step in next_steps:
            bits = [f"<b>{safe(step.get('name', ''))}</b>", safe(plainify(str(step.get("why", ""))))]
            if step.get("contact"):
                bits.append(safe(step["contact"]))
            if step.get("url"):
                bits.append(_link(step["url"], "Website"))
            story.append(KeepTogether([Paragraph("<br/>".join(b for b in bits if b), st["body"]), Spacer(1, 6)]))

    # ---- sources
    sources = summary.get("sources") or []
    if sources:
        story.append(Paragraph("Sources", st["h1"]))
        for src in sources:
            read = f", read {safe(str(src['retrieved_at'])[:10])}" if src.get("retrieved_at") else ""
            sample = " (saved sample data)" if src.get("sample") else ""
            story.append(Paragraph(f"{safe(src.get('label', ''))}{read}{sample}<br/>{_link(src.get('url'), str(src.get('url', '')))}", st["small"]))
            story.append(Spacer(1, 3))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.8 * inch,
        title=f"Professor Fritts plan: {intake.get('building_name') or intake.get('address') or 'building'}",
        author="Professor Fritts",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
