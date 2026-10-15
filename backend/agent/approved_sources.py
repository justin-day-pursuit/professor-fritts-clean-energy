"""
Load the approved-sources list the v3 validator and prompt rely on.

The file is the allowlist of official NYC, New York State, federal, and Con Edison
pages, plus DSIRE marked finder-only. Edit the YAML to add a page; do not hard-code
URLs in the checker.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_SOURCES_PATH = Path(__file__).resolve().parent.parent / "data" / "approved_sources.yaml"

_JURISDICTIONS = {"nyc", "ny_state", "federal", "con_edison"}
_ROLES = {"official", "finder_only"}


def load_approved_sources(path: Path | None = None) -> list[dict[str, Any]]:
    """
    Read approved_sources.yaml and return one dict per page.

    Each dict has id, name, url, jurisdiction, and role. Raise ValueError if an
    entry is missing a field or uses a jurisdiction or role this version does not know.
    """
    source_path = path or _SOURCES_PATH
    raw = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    entries = raw.get("sources") if isinstance(raw, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"No sources list in {source_path}")

    loaded: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"Source entry is not a mapping: {entry!r}")
        missing = [key for key in ("id", "name", "url", "jurisdiction", "role") if not entry.get(key)]
        if missing:
            raise ValueError(f"Source {entry.get('id')!r} is missing {', '.join(missing)}")
        jurisdiction = str(entry["jurisdiction"])
        role = str(entry["role"])
        if jurisdiction not in _JURISDICTIONS:
            raise ValueError(f"Source {entry['id']!r} has unknown jurisdiction {jurisdiction!r}")
        if role not in _ROLES:
            raise ValueError(f"Source {entry['id']!r} has unknown role {role!r}")
        loaded.append(
            {
                "id": str(entry["id"]),
                "name": str(entry["name"]),
                "url": str(entry["url"]),
                "jurisdiction": jurisdiction,
                "role": role,
            }
        )
    return loaded
