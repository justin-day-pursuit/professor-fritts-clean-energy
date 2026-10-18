"""
Live check of incentives and rules for NYC public buildings (v7).

Incentive status is a legal and program fact that changes, and no free API publishes it in a clean form. So the
programs live in a curated register (backend/data/incentive_programs.json) that people maintain, and this module
re-reads each program's OFFICIAL page on every run and verifies it:

  - the page must load, and must still contain every phrase the register lists for it;
  - then the recorded status is kept, and the retrieved date is today;
  - if the page cannot be read (blocked, down) or the phrases are gone, the program is reported as "uncertain" with
    the reason, and the plan leaves it out of net cost.

The quote saved with each program is a real sentence cut from the live page. A federal deadline that has passed
turns the program to "closed" without anyone editing the register. Pages that carry hidden instructions are handled
by the existing quarantine in tools/ny_rules_rates.py.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx

from tools.base import ToolResult
from tools.web import get_with_retry

REGISTER_PATH = Path(__file__).resolve().parent.parent / "data" / "incentive_programs.json"
USER_AGENT = "Mozilla/5.0 (compatible; ProfessorFritts/1.0; +public-building-energy-planner)"
TIMEOUT_SECONDS = 25
REGISTER_SOURCE_URL = "https://www.irs.gov/credits-deductions/elective-pay-and-transferability"


class _TextOnly(HTMLParser):
    """Collects the visible text of a web page, skipping scripts and styles."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def page_text(html: str) -> str:
    """The visible text of an HTML page as one string."""
    parser = _TextOnly()
    parser.feed(html)
    return " ".join(parser.parts).replace(" ", " ")


def load_register() -> list[dict[str, Any]]:
    """The curated list of programs."""
    return list(json.loads(REGISTER_PATH.read_text(encoding="utf-8"))["programs"])


def applies(entry: dict[str, Any], profile: dict[str, Any]) -> bool:
    """A program applies to everyone ("all") or only to a kind of building: "doe" means a public school."""
    scope = entry.get("applies_to", "all")
    if scope == "all":
        return True
    if scope == "doe":
        owner = str(profile.get("owner_agency") or "").lower()
        kind = str(profile.get("building_type") or "").lower()
        return owner == "doe" or "school" in kind
    return True


def quote_for(text: str, phrases: list[str]) -> str:
    """
    One real sentence from the page that holds ALL the phrases, or an empty string.

    Menus and page headers also contain the words, so the sentence must read like prose: 8 to 60 words and ending
    in a period. The first such sentence is used.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        words = sentence.split()
        lowered = sentence.lower()
        if all(p.lower() in lowered for p in phrases) and 8 <= len(words) <= 60 and sentence.rstrip().endswith("."):
            return sentence.strip()
    return ""


def read_page(url: str) -> tuple[str | None, str]:
    """(visible text, "") when the page loads, or (None, reason) when it cannot be read."""
    try:
        response = get_with_retry(
            url, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=TIMEOUT_SECONDS
        )
    except (httpx.HTTPError, ValueError) as exc:
        return None, f"the page could not be reached ({type(exc).__name__})"
    if response.status_code != 200:
        return None, f"the page answered HTTP {response.status_code}, which blocks automated reading"
    return page_text(response.text), ""


def verify_program(entry: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    """
    Re-read one program's official page and return the program as the tool reports it.

    The register's recorded status is kept only when every required phrase is still on the page (and, for a
    program with a statute page, on that page too). A deadline that has passed closes the program.
    """
    today = today or datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status = entry["recorded_status"]
    note = entry.get("status_note", "")
    problems: list[str] = []
    quote = ""
    page_hash = ""

    checks = [(entry["source_url"], entry.get("verify_phrases", []), True)]
    if entry.get("statute_url") and entry.get("statute_verify_phrases"):
        checks.append((entry["statute_url"], entry["statute_verify_phrases"], False))
    for url, phrases, is_main in checks:
        if not phrases:
            # Nothing to verify (a page that blocks programs): the recorded "uncertain" note stands.
            continue
        text, reason = read_page(url)
        if text is None:
            problems.append(f"{url}: {reason}")
            continue
        missing = [p for p in phrases if p.lower() not in text.lower()]
        if missing:
            problems.append(f"{url}: no longer contains {', '.join(repr(m) for m in missing)}")
            continue
        if is_main:
            quote = quote_for(text, entry.get("quote_phrases") or phrases)
            page_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    if problems:
        status = "uncertain"
        note = (
            "Could not confirm today: " + "; ".join(problems)
            + f". Last recorded as '{entry['recorded_status']}' on {entry.get('as_of')}; verify before relying on it. "
            + note
        )
    deadline = entry.get("deadline")
    if deadline and today > date.fromisoformat(deadline) and status == "open":
        status = "closed"
        note = f"The deadline of {deadline} has passed. " + note

    program: dict[str, Any] = {
        "name": entry["name"],
        "status": status,
        "status_note": note,
        "source_url": entry["source_url"],
        "retrieved_at": now,
    }
    if deadline:
        program["deadline"] = deadline
    if entry.get("statute_url"):
        program["statute_url"] = entry["statute_url"]
    if quote:
        program["quote"] = quote
        program["page_hash"] = page_hash
    return program


def fetch_live_incentives(profile: dict[str, Any]) -> ToolResult:
    """Verify every program that applies to this building against its official page and return the list."""
    programs = [verify_program(entry) for entry in load_register() if applies(entry, profile)]
    flags = ["incentives_curated_register"]
    if any(p["status"] == "uncertain" for p in programs):
        flags.append("incentive_status_uncertain")
    return ToolResult(
        tool="search_ny_incentives_and_rules",
        data={"programs": programs},
        source_url=REGISTER_SOURCE_URL,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version="curated-register-live-verified",
        mock=False,
        flags=flags,
    )
