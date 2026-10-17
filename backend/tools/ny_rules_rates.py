"""
Utility rates, tariff and NY incentives search tools (group 3) — live EIA price in v1, mock program lists.

v4: when a saved incentive is missing or older than 7 days, this tool saves the
pre-fetched live status and quoted text into the versioned cache, with a page hash.
"""

from __future__ import annotations

import hashlib
from typing import Any

from mocks.mock_mode import get_tool_mode, require_mock_or_fixture
from tools.base import ToolResult
from tools.cache import get_reference_cache, is_stale
from tools.injection import has_hidden_instructions
from tools.live_incentives import fetch_live_incentives
from tools.live_rates import fetch_live_utility_rates
from tools.live_tariff import fetch_live_tariff
from tools.upsert_cache import upsert_reference_cache


def get_utility_rates(case: str, profile: dict[str, Any] | None = None) -> ToolResult:
    """Return the live EIA price in live mode, or the saved tariff in mock mode."""
    if get_tool_mode() == "live":
        return fetch_live_utility_rates(profile or {})
    return require_mock_or_fixture(case, "get_utility_rates")


def quote_page_hash(quote: str) -> str:
    """SHA-256 of the exact quoted page text saved with a refreshed incentive."""
    return hashlib.sha256(quote.encode("utf-8")).hexdigest()


def _refresh_stale_program(program: dict[str, Any], source_url: str) -> None:
    """
    Save a new cache version when this program's saved row is missing or older than 7 days.

    The live status and live_quote come from the pre-fetched page in the fixture.
    Programs without a record_id are left alone. A fresh row is not written again.
    """
    record_id = str(program.get("record_id") or "").strip()
    if not record_id:
        return
    live_status = str(program.get("live_status") or program.get("status") or "").strip()
    if not live_status:
        return
    quote = str(program.get("live_quote") or "")
    cache = get_reference_cache()
    latest = cache.get_latest(record_id) if hasattr(cache, "get_latest") else None
    if latest is not None and not is_stale(str(latest.get("retrieved_at") or ""), "incentives"):
        return
    page_hash = quote_page_hash(quote or live_status)
    program["page_hash"] = page_hash
    upsert_reference_cache(
        record_id,
        {
            "name": program.get("name"),
            "status": live_status,
            "live_quote": quote,
        },
        source_url=source_url,
        retrieved_at=str(program.get("live_retrieved_at") or program.get("retrieved_at") or ""),
        page_hash=page_hash,
        freshness_kind="incentives",
    )


def _quarantine_entry(program: dict[str, Any], source_url: str) -> dict[str, Any]:
    """
    What the agent is told about a program page that carried hidden instructions.

    Only the name and the page address are kept, so the plan can say the page was ignored.
    None of the page's own text (status, amounts, the injected sentence) is passed on.
    """
    return {
        "name": str(program.get("name") or "Unnamed program"),
        "source_url": str(program.get("source_url") or source_url),
        "reason": "Page contains hidden instructions; ignored and not saved.",
    }


def search_ny_incentives_and_rules(case: str, profile: dict[str, Any] | None = None) -> ToolResult:
    """
    Return saved incentive snippets, and refresh any program whose cache row is stale.

    A conflict between the cached status and the live page is flagged cached_live_conflict.
    The refresh writes the live status, the exact quote, and a page hash.

    v6: a program whose text carries hidden instructions is moved to data["quarantined"] with only
    its name and page address, is never refreshed into the cache, and adds the flag
    hidden_instruction_pattern. A program where DSIRE (a finder, not a source) disagrees with the
    official page adds finder_official_conflict; the official status is the one used and saved.
    """
    if get_tool_mode() == "live":
        # Live: the curated register, each program's official page re-read and verified today (tools/live_incentives.py).
        result = fetch_live_incentives(profile or {})
    else:
        result = require_mock_or_fixture(case, "search_ny_incentives_and_rules")
    flags = list(result.flags)
    programs: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for raw in result.data.get("programs", []):
        if not isinstance(raw, dict):
            continue
        program = dict(raw)
        if has_hidden_instructions(program):
            quarantined.append(_quarantine_entry(program, result.source_url))
            if "hidden_instruction_pattern" not in flags:
                flags.append("hidden_instruction_pattern")
            continue
        if program.get("conflict") and "cached_live_conflict" not in flags:
            flags.append("cached_live_conflict")
        if program.get("finder_status") and "finder_official_conflict" not in flags:
            if str(program["finder_status"]).lower() != str(program.get("status") or "").lower():
                flags.append("finder_official_conflict")
        _refresh_stale_program(program, str(program.get("source_url") or result.source_url))
        programs.append(program)
    data = dict(result.data)
    data["programs"] = programs
    if quarantined:
        data["quarantined"] = quarantined
    return result.model_copy(update={"flags": flags, "data": data})


def get_utility_tariff(case: str, profile: dict[str, Any] | None = None) -> ToolResult:
    """
    Return the named utility tariff (OpenEI-style) with its effective date and price ranges.

    Mock only until v8: it always reads the saved case file, even in a live run, and the harness
    marks it 'mock_data_in_live_run' so the plan never presents it as live data. The tariff is
    flagged for the user to confirm, because picking the wrong tariff skews savings widely.
    """
    if get_tool_mode() == "live":
        return fetch_live_tariff(profile or {})
    return require_mock_or_fixture(case, "get_utility_tariff")
