"""
upsert_reference_cache — the only write tool.

Saves fresh results when cached data is stale or missing. Validates the source
against approved_sources.yaml. Returns the record_id, version, and changed flag.
"""

from __future__ import annotations

from typing import Any

from tools.approved_sources import is_approved_source
from tools.base import ToolResult
from tools.cache import FRESHNESS_DAYS, get_reference_cache


def upsert_reference_cache(
    record_id: str,
    payload: dict[str, Any],
    *,
    source_url: str = "",
    retrieved_at: str = "",
    page_hash: str = "",
    freshness_kind: str = "incentives",
) -> ToolResult:
    """
    Save a fresh result to the versioned cache.

    Rejects:
    - Missing or non-approved source_url
    - User input or model estimates (no source_url)
    """
    if not source_url:
        return ToolResult(
            tool="upsert_reference_cache",
            data={"error": "source_url is required"},
            flags=["rejected_no_source"],
        )

    if not is_approved_source(source_url):
        return ToolResult(
            tool="upsert_reference_cache",
            data={"error": f"Source {source_url} is not on the approved list"},
            flags=["rejected_unapproved_source"],
        )

    limit_days = FRESHNESS_DAYS.get(freshness_kind, FRESHNESS_DAYS["default"])

    cache = get_reference_cache()
    result = cache.put(
        record_id,
        payload,
        source_url=source_url,
        retrieved_at=retrieved_at,
        page_hash=page_hash,
        freshness_limit_days=limit_days,
    )

    flags: list[str] = []
    if result.get("changed"):
        flags.append("cache_record_changed")
    if result.get("pending"):
        flags.append("cache_pending_human_review")

    return ToolResult(
        tool="upsert_reference_cache",
        data=result,
        source_url=source_url,
        retrieved_at=retrieved_at,
        dataset_version=f"cache-v{result['version']}",
        flags=flags,
    )
