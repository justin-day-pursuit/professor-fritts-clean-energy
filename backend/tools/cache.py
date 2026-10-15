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


# These tools read the user's own intake or do arithmetic, so they have no retrieval date by design.
TOOLS_WITHOUT_RETRIEVAL_DATE = frozenset({"get_building_profile", "calculate"})


def is_stale_for_tool(tool_name: str, retrieved_at: str, kind: str) -> bool:
    """
    Staleness for one tool result: is_stale, except tools with no external source are never stale.

    Without this exception an empty retrieved_at counts as "unknown age = stale", so the intake and
    calculate results were flagged stale_data on every run.
    """
    if tool_name in TOOLS_WITHOUT_RETRIEVAL_DATE:
        return False
    return is_stale(retrieved_at, kind)


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


def _payload_amount(payload: dict[str, Any]) -> float | None:
    """Dollar figure on a cache row, when the payload has one."""
    for key in ("amount", "incentive_amount"):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        return float(value)
    return None


def _payload_deadline(payload: dict[str, Any]) -> str:
    """ISO date string for a program deadline, or empty when the row has none."""
    value = payload.get("deadline")
    if isinstance(value, str):
        return value.strip()
    return ""


class DjangoCacheBackend(ReferenceCache):
    """
    SQLite-backed cache using the CacheRecord Django model (v4+).

    Append-only versioned writes. Rollback soft-deletes the latest version.
    Safe-change rule: cautious changes auto-save, favorable changes save as pending.
    """

    def get(self, record_id: str) -> dict[str, Any] | None:
        """Return the latest non-rolled-back, non-pending version's data."""
        from core.models import CacheRecord

        row = (
            CacheRecord.objects.filter(record_id=record_id, rolled_back=False, pending=False)
            .order_by("-version")
            .first()
        )
        return row.data if row else None

    def get_latest(self, record_id: str, *, include_pending: bool = False) -> dict[str, Any] | None:
        """Return the latest version with full metadata, optionally including pending."""
        from core.models import CacheRecord

        qs = CacheRecord.objects.filter(record_id=record_id, rolled_back=False)
        if not include_pending:
            qs = qs.filter(pending=False)
        row = qs.order_by("-version").first()
        if not row:
            return None
        return {
            "record_id": row.record_id,
            "version": row.version,
            "source_url": row.source_url,
            "retrieved_at": row.retrieved_at.isoformat(),
            "data": row.data,
            "page_hash": row.page_hash,
            "changed": row.changed,
            "pending": row.pending,
        }

    def put(
        self,
        record_id: str,
        payload: dict[str, Any],
        *,
        source_url: str = "",
        retrieved_at: str = "",
        page_hash: str = "",
        freshness_limit_days: int = 7,
    ) -> dict[str, Any]:
        """
        Append a new version. Apply the safe-change rule:
        - Cautious changes (e.g. open→closed) auto-save.
        - Favorable changes (e.g. closed→open) save as pending.
        Returns {record_id, version, changed, pending, previous_status}.
        """
        from core.models import CacheRecord

        prev = (
            CacheRecord.objects.filter(record_id=record_id)
            .order_by("-version")
            .first()
        )
        prev_version = prev.version if prev else 0
        prev_active = (
            CacheRecord.objects.filter(record_id=record_id, rolled_back=False)
            .order_by("-version")
            .first()
        )
        prev_payload = prev_active.data if prev_active else {}
        prev_status = prev_payload.get("status", "") if prev_payload else ""

        changed = prev is None or prev.data != payload
        pending = self._is_favorable_change(prev_payload, payload) if changed else False

        dt = parse_iso_datetime(retrieved_at) or datetime.now(timezone.utc)
        row = CacheRecord.objects.create(
            record_id=record_id,
            version=prev_version + 1,
            source_url=source_url,
            retrieved_at=dt,
            freshness_limit_days=freshness_limit_days,
            data=payload,
            page_hash=page_hash,
            previous_status=prev_status,
            changed=changed,
            pending=pending,
        )
        return {
            "record_id": record_id,
            "version": row.version,
            "changed": changed,
            "pending": pending,
            "previous_status": prev_status,
        }

    def rollback(self, record_id: str) -> dict[str, Any] | None:
        """
        Soft-delete the latest version and return the restored previous version.
        Returns None if no versions remain after rollback.
        """
        from core.models import CacheRecord

        latest = (
            CacheRecord.objects.filter(record_id=record_id, rolled_back=False)
            .order_by("-version")
            .first()
        )
        if not latest:
            return None
        latest.rolled_back = True
        latest.save(update_fields=["rolled_back"])
        return self.get_latest(record_id)

    def confirm_pending(self, record_id: str, version: int) -> bool:
        """Confirm a pending record (human approval of a favorable change)."""
        from core.models import CacheRecord

        updated = CacheRecord.objects.filter(
            record_id=record_id, version=version, pending=True
        ).update(pending=False)
        return updated > 0

    def versions(self, record_id: str) -> list[dict[str, Any]]:
        """List all stored versions including rolled-back ones, for debugging."""
        from core.models import CacheRecord

        rows = CacheRecord.objects.filter(record_id=record_id).order_by("version")
        return [
            {
                "version": r.version,
                "data": r.data,
                "source_url": r.source_url,
                "retrieved_at": r.retrieved_at.isoformat(),
                "page_hash": r.page_hash,
                "changed": r.changed,
                "pending": r.pending,
                "rolled_back": r.rolled_back,
            }
            for r in rows
        ]

    @staticmethod
    def _is_favorable_change(old_payload: dict[str, Any], new_payload: dict[str, Any]) -> bool:
        """
        A change that makes a plan more cautious saves immediately.
        A change that makes a plan more favorable waits for a person.

        Cautious: open to closed, a smaller amount, or an earlier deadline.
        Favorable: closed to open, a larger amount, or a later deadline.
        Status wins over amount and deadline, so closing a program still saves
        even if the dollar figure went up. The first write has no old row and saves.
        """
        old_status = str(old_payload.get("status") or "").lower().strip()
        new_status = str(new_payload.get("status") or "").lower().strip()
        if old_status and new_status:
            if new_status in ("closed", "expired", "suspended"):
                return False
            if old_status in ("closed", "expired", "suspended") and new_status in ("open", "active"):
                return True

        old_amount = _payload_amount(old_payload)
        new_amount = _payload_amount(new_payload)
        if old_amount is not None and new_amount is not None and new_amount != old_amount:
            return new_amount > old_amount

        old_deadline = _payload_deadline(old_payload)
        new_deadline = _payload_deadline(new_payload)
        if old_deadline and new_deadline and old_deadline != new_deadline:
            return new_deadline > old_deadline
        return False


_default_cache: ReferenceCache | None = None


def get_reference_cache() -> ReferenceCache:
    """Return the process-wide cache (Django-backed in v4+, JSON file as fallback)."""
    global _default_cache
    if _default_cache is None:
        _default_cache = DjangoCacheBackend()
    return _default_cache
