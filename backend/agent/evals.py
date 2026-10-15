"""
Eval runner (v6): run every fixture case that has an expected.json and compare the run to it.

Each mocks/fixtures/<case>/expected.json is written before the case is run and lists what must be
true afterwards. Every key is optional:

  status               done | partial | needs_input | failed
  stop_reason          the Check 1 stop reason, for example "out_of_scope"
  check4_passed        true when every claim must pass Check 4 (a partial run can still pass it)
  flags_include        note flags the run must raise
  roadmap_includes     lowercase text the roadmap Markdown must contain
  roadmap_excludes     lowercase text it must not contain (for example an injected "50% grant")
  message_includes     lowercase text the stop message or question must contain
  message_excludes     lowercase text it must not contain
  cache_latest_status  {record_id: status} the cache must hold afterwards
  cache_must_not_have_records  record ids this run must not save (older rows are ignored)
  cache_must_not_have_sources  page addresses this run must not save from (older rows are ignored)
  seed_cache           cache rows this case starts from; each record is replaced so a re-run starts fresh

The runner always uses the scripted model and mock tools, so it needs no key and no network.
Used by `python manage.py run_evals` and by tests/test_v6_evals.py.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.conf import settings

from mocks.catalog import FIXTURES_ROOT, load_case


@dataclass
class EvalResult:
    """Outcome of one case: passed when failures is empty."""

    case: str
    status: str = ""
    failures: list[str] = field(default_factory=list)
    run_id: int | None = None
    llm_provider: str = ""
    tool_mode: str = ""

    @property
    def passed(self) -> bool:
        return not self.failures


def list_eval_cases() -> list[str]:
    """Every fixture folder with an expected.json, in name order."""
    return sorted(p.parent.name for p in FIXTURES_ROOT.glob("*/expected.json"))


def load_expected(case: str) -> dict[str, Any]:
    """Read one case's expected.json (the _comment key is ignored)."""
    raw = json.loads((FIXTURES_ROOT / case / "expected.json").read_text(encoding="utf-8"))
    raw.pop("_comment", None)
    return raw


def _cache_row_ids() -> set[int]:
    """Primary keys already in the cache, so a check can ignore rows from an earlier run."""
    from core.models import CacheRecord

    return set(CacheRecord.objects.values_list("pk", flat=True))


def _seed_cache(rows: list[dict[str, Any]]) -> None:
    """Replace each seeded record with the row this case starts from, including on a re-run."""
    from core.models import CacheRecord
    from tools.cache import get_reference_cache

    cache = get_reference_cache()
    for row in rows:
        CacheRecord.objects.filter(record_id=row["record_id"]).delete()
        cache.put(
            row["record_id"],
            row["payload"],
            source_url=row.get("source_url", ""),
            retrieved_at=row.get("retrieved_at", ""),
        )


def _check_cache(expected: dict[str, Any], failures: list[str], before_ids: set[int]) -> None:
    """Compare the versioned cache with the cache_* expectations. Only rows new since before_ids count as saves."""
    from core.models import CacheRecord
    from tools.cache import get_reference_cache

    cache = get_reference_cache()
    for record_id, status in (expected.get("cache_latest_status") or {}).items():
        latest = cache.get_latest(record_id)
        got = (latest or {}).get("data", {}).get("status")
        if got != status:
            failures.append(f"cache {record_id}: latest status {got!r}, expected {status!r}")
    saved_now = CacheRecord.objects.exclude(pk__in=before_ids)
    for record_id in expected.get("cache_must_not_have_records") or []:
        if saved_now.filter(record_id=record_id).exists():
            failures.append(f"cache {record_id}: saved, but it must never be saved")
    for source in expected.get("cache_must_not_have_sources") or []:
        if saved_now.filter(source_url=source).exists():
            failures.append(f"cache: something was saved from {source}")


def _includes(label: str, text: str, wanted: list[str], failures: list[str], *, present: bool) -> None:
    """Record each phrase that is missing (present=True) or wrongly there (present=False)."""
    for phrase in wanted:
        if (phrase.lower() in text) != present:
            failures.append(f"{label} {'is missing' if present else 'must not contain'} {phrase!r}")


def run_eval_case(case: str, *, llm_provider: str = "scripted", tool_mode: str = "mock") -> EvalResult:
    """Run one case and list every expectation it misses. Defaults stay on the scripted model and mock tools."""
    from agent.harness import run_harness
    from core import services

    expected = load_expected(case)
    result = EvalResult(case=case, llm_provider=llm_provider, tool_mode=tool_mode)
    before_ids = _cache_row_ids()
    _seed_cache(expected.get("seed_cache") or [])

    profile, question = load_case(case)
    previous_mode = getattr(settings, "TOOL_MODE", "mock")
    settings.TOOL_MODE = tool_mode
    try:
        session = services.create_session(profile=profile, fixture_case=case)
        services.add_message(session, role="user", content=question)
        run = run_harness(session, question, llm_provider=llm_provider, tool_mode=tool_mode)
    finally:
        settings.TOOL_MODE = previous_mode
    result.run_id = run.pk
    result.llm_provider = run.llm_provider
    result.tool_mode = run.tool_mode

    output = run.output or {}
    flags = run.flags or {}
    result.status = run.status
    failures = result.failures

    if "status" in expected and run.status != expected["status"]:
        failures.append(f"status {run.status!r}, expected {expected['status']!r}")
    if "stop_reason" in expected and output.get("stop_reason") != expected["stop_reason"]:
        failures.append(f"stop_reason {output.get('stop_reason')!r}, expected {expected['stop_reason']!r}")
    if "check4_passed" in expected:
        got = bool((flags.get("check4") or {}).get("passed"))
        if got != expected["check4_passed"]:
            issues = (flags.get("check4") or {}).get("details", {}).get("issues") or []
            failures.append(f"check4 passed={got}, expected {expected['check4_passed']}; issues: {issues}")

    note_flags = (output.get("notes") or {}).get("flags") or []
    for flag in expected.get("flags_include") or []:
        if flag not in note_flags:
            failures.append(f"flag {flag!r} not raised")

    markdown = str(output.get("markdown") or "").lower()
    _includes("roadmap", markdown, expected.get("roadmap_includes") or [], failures, present=True)
    _includes("roadmap", markdown, expected.get("roadmap_excludes") or [], failures, present=False)

    message = str(output.get("question") or output.get("error") or "").lower()
    _includes("message", message, expected.get("message_includes") or [], failures, present=True)
    _includes("message", message, expected.get("message_excludes") or [], failures, present=False)

    _check_cache(expected, failures, before_ids)
    return result


def run_all_evals() -> list[EvalResult]:
    """Run every case in list_eval_cases() and return the results in the same order."""
    return [run_eval_case(case) for case in list_eval_cases()]
