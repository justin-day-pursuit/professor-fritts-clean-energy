"""
Reference cache for freshness checks — in-memory or a local JSON file under .data/.

Later blocks may swap in a hosted database; v0 never connects to Supabase (Postgres comes in v7).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

# How long each kind of cached record is considered fresh (Check 2 compares fixture dates to these).
FRESHNESS_DAYS: dict[str, int] = {
    "incentives": 7,
    "utility_rates": 90,
    "building_records": 180,
    "solar_production": 365,
    "hazard": 365,
    "default": 180,
}


def parse_iso_datetime(value: str) -> datetime | None:
    """Turn a fixture retrieved_at string into a timezone-aware datetime, or None if blank."""
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_stale(retrieved_at: str, kind: str) -> bool:
    """
    Return True when retrieved_at is older than the freshness window for this data kind.

    Used by Check 2/3 to set the stale flag without blocking the run.
    """
    dt = parse_iso_datetime(retrieved_at)
    if dt is None:
        return True
    limit_days = FRESHNESS_DAYS.get(kind, FRESHNESS_DAYS["default"])
    age = datetime.now(timezone.utc) - dt
    return age > timedelta(days=limit_days)


class ReferenceCache(ABC):
    """Abstract cache — get, put, and list versions for a record id."""

    @abstractmethod
    def get(self, record_id: str) -> dict[str, Any] | None:
        """Return the latest payload for record_id, or None if missing."""

    @abstractmethod
    def put(self, record_id: str, payload: dict[str, Any]) -> None:
        """Store a new version (append-only in later blocks; v0 overwrites one slot per id)."""

    @abstractmethod
    def versions(self, record_id: str) -> list[dict[str, Any]]:
        """List stored versions for debugging; v0 keeps at most one entry per id."""


class InMemoryReferenceCache(ReferenceCache):
    """Simple dict-backed cache for tests and ephemeral runs."""

    def __init__(self) -> None:
        self._store: dict[str, list[dict[str, Any]]] = {}

    def get(self, record_id: str) -> dict[str, Any] | None:
        versions = self._store.get(record_id)
        if not versions:
            return None
        return versions[-1]

    def put(self, record_id: str, payload: dict[str, Any]) -> None:
        self._store.setdefault(record_id, []).append(payload)

    def versions(self, record_id: str) -> list[dict[str, Any]]:
        return list(self._store.get(record_id, []))


class JsonFileReferenceCache(ReferenceCache):
    """
    Persists cache entries to backend/.data/cache.json for local dev.

    The file is gitignored; delete it to reset cached fixture metadata.
    """

    def __init__(self, path: Path | None = None) -> None:
        data_dir = getattr(settings, "DATA_DIR", Path(__file__).resolve().parent.parent / ".data")
        self._path = path or (data_dir / "cache.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, list[dict[str, Any]]] = self._load()

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def get(self, record_id: str) -> dict[str, Any] | None:
        versions = self._data.get(record_id)
        if not versions:
            return None
        return versions[-1]

    def put(self, record_id: str, payload: dict[str, Any]) -> None:
        self._data.setdefault(record_id, []).append(payload)
        self._save()

    def versions(self, record_id: str) -> list[dict[str, Any]]:
        return list(self._data.get(record_id, []))


_default_cache: ReferenceCache | None = None


def get_reference_cache() -> ReferenceCache:
    """Return the process-wide cache (JSON file in dev, same interface in tests)."""
    global _default_cache
    if _default_cache is None:
        _default_cache = JsonFileReferenceCache()
    return _default_cache
