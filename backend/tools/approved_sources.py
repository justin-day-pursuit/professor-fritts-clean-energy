"""
Approved-sources allowlist — load approved_sources.yaml and validate source URLs.

The cache and upsert tool reject any source_url whose domain is not on this list.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml


def _load_yaml() -> list[dict[str, str]]:
    path = Path(__file__).resolve().parent.parent / "data" / "approved_sources.yaml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return raw.get("sources", [])


@lru_cache(maxsize=1)
def approved_domains() -> dict[str, dict[str, str]]:
    """Return {domain: {kind, description}} for every approved source."""
    return {entry["domain"]: entry for entry in _load_yaml()}


def is_approved_source(source_url: str) -> bool:
    """True when the URL's domain (or a parent domain) is on the approved list."""
    if not source_url:
        return False
    try:
        host = urlparse(source_url).hostname or ""
    except Exception:
        return False
    host = host.lower().lstrip("www.")
    for domain in approved_domains():
        if host == domain or host.endswith("." + domain):
            return True
    return False


def source_kind(source_url: str) -> str | None:
    """Return the kind (incentive, rule, etc.) for an approved URL, or None."""
    if not source_url:
        return None
    try:
        host = urlparse(source_url).hostname or ""
    except Exception:
        return None
    host = host.lower().lstrip("www.")
    for domain, entry in approved_domains().items():
        if host == domain or host.endswith("." + domain):
            return entry.get("kind")
    return None
