"""
v6 goalpost: every eval case passes in mock mode.

One test per fixture folder that has an expected.json, so a new case is picked up without editing
this file. The expectations themselves live in each case's expected.json (see agent/evals.py).
"""

from __future__ import annotations

import pytest

from agent.evals import _cache_row_ids, _check_cache, _seed_cache, list_eval_cases, run_eval_case


def test_all_nine_eval_cases_are_present():
    """The PRD's three cases plus the six v6 extra cases (outside NYC x2, no budget, DSIRE, flood, landmark)."""
    assert len(list_eval_cases()) >= 9


@pytest.mark.parametrize("case", list_eval_cases())
def test_eval_case_passes_in_mock_mode(case):
    """Run the case with the scripted model and mock tools and compare it to its expected.json."""
    result = run_eval_case(case)
    assert result.passed, "\n".join(result.failures)


def test_seed_cache_replaces_a_newer_row():
    """A second eval run puts the stale starting row back, instead of keeping whatever was saved last."""
    from tools.cache import get_reference_cache

    cache = get_reference_cache()
    record_id = "incentive:seed-reset-test"
    cache.put(
        record_id,
        {"status": "closed"},
        source_url="https://example.test/fictional/seed-reset",
        retrieved_at="2026-10-01T00:00:00Z",
    )
    _seed_cache([{
        "record_id": record_id,
        "payload": {"status": "open"},
        "source_url": "https://example.test/fictional/seed-reset",
        "retrieved_at": "2026-06-03T12:00:00Z",
    }])
    latest = cache.get_latest(record_id)
    assert latest is not None and latest["data"]["status"] == "open"


def test_an_older_cache_row_does_not_fail_must_not_have():
    """Rows saved before this run are not counted. A new row with the same id is."""
    from tools.cache import get_reference_cache

    cache = get_reference_cache()
    record_id = "incentive:old-row-must-not-count"
    source = "https://example.test/fictional/old-row"
    cache.put(record_id, {"status": "open"}, source_url=source, retrieved_at="2026-01-01T00:00:00Z")
    before = _cache_row_ids()
    expected = {
        "cache_must_not_have_records": [record_id],
        "cache_must_not_have_sources": [source],
    }
    failures: list[str] = []
    _check_cache(expected, failures, before)
    assert failures == []

    cache.put(record_id, {"status": "open"}, source_url=source, retrieved_at="2026-02-01T00:00:00Z")
    failures = []
    _check_cache(expected, failures, before)
    assert any(record_id in failure for failure in failures)
    assert any(source in failure for failure in failures)
