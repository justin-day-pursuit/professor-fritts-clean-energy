"""
Approved-sources allowlist — load approved_sources.yaml and validate source URLs.

The cache and upsert tool reject any source_url whose domain is not on this list.
DSIRE is finder-only: it can point at a program, but it is not a source we save.
example.test is allowed only while tools are in mock mode, for saved eval fixtures.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from mocks.mock_mode import get_tool_mode


def _load_yaml() -> list[dict[str, str]]:
    path = Path(__file__).resolve().parent.parent / "data" / "approved_sources.yaml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return raw.get("sources", [])


@lru_cache(maxsize=1)
def approved_domains() -> dict[str, dict[str, str]]:
    """Return {domain: {kind, description}} for every approved source."""
    return {entry["domain"]: entry for entry in _load_yaml()}


def _host(source_url: str) -> str:
    """Hostname without a leading www, or an empty string when the URL has none."""
    try:
        host = urlparse(source_url).hostname or ""
    except Exception:
        return ""
    return host.lower().lstrip("www.")


def source_entry(source_url: str) -> dict[str, Any] | None:
    """
    The allowlist row for this URL, or None when it must not be saved.

    example.test matches only in mock mode so eval fixtures can be stored.
    A live run does not get that exception.
    """
    if not source_url:
        return None
    host = _host(source_url)
    if not host:
        return None
    if host == "example.test" or host.endswith(".example.test"):
        if get_tool_mode() != "mock":
            return None
        return {"domain": host, "role": "official", "kind": "fixture"}
    for domain, entry in approved_domains().items():
        if host == domain or host.endswith("." + domain):
            return entry
    return None


def is_finder_only(source_url: str) -> bool:
    """True when the page is on the list only as a finder, such as DSIRE."""
    entry = source_entry(source_url)
    return bool(entry and entry.get("role") == "finder_only")


def is_approved_source(source_url: str) -> bool:
    """True when this URL may be saved: on the list, and not finder-only."""
    entry = source_entry(source_url)
    return bool(entry) and entry.get("role") != "finder_only"


def source_kind(source_url: str) -> str | None:
    """Return the kind (incentive, rule, etc.) for an approved URL, or None."""
    entry = source_entry(source_url)
    if not entry:
        return None
    return entry.get("kind")
