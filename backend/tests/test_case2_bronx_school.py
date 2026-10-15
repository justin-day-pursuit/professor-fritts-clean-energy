"""
Eval case 2 (edge case), NYC version: a fictional Bronx elementary school with no bills, an unknown roof
age, a budget with no year or type, and a saved incentive record that disagrees with the live page.

These run the scripted model on saved fixtures, so they need no network and no API key. The stale-record
refresh itself (saving the new "closed" version to the cache) arrives with v4; here we check that the
conflict is detected, shown, and kept out of net cost.
"""

from __future__ import annotations

import pytest

from agent.claims import RoadmapPayload
from agent.coverage import check_coverage
from agent.harness import run_harness
from core import services
from core.models import Run
from mocks.catalog import load_case

CASE = "case2_bronx_school"


@pytest.fixture(autouse=True)
def scripted_env(monkeypatch):
    """Scripted model and mock tools, so nothing here touches the network."""
    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("TOOL_MODE", "mock")
    from django.conf import settings

    settings.LLM_PROVIDER = "scripted"
    settings.TOOL_MODE = "mock"


@pytest.fixture
def run_and_payload():
    """Run case 2 end to end and return the finished run plus its roadmap."""
    from tools.cache import get_reference_cache

    cache = get_reference_cache()
    record_id = "incentive:nyserda-school-solar"
    # Seed the 120-day-old 'open' record if not present, as described in case 2 spec
    if not cache.versions(record_id):
        cache.put(
            record_id,
            {"name": "NYSERDA school solar program (fictional stand-in)", "status": "open"},
            source_url="https://example.test/fictional/case2/incentives",
            retrieved_at="2026-06-03T12:00:00Z",
        )
    profile, question = load_case(CASE)
    session = services.create_session(profile=profile, fixture_case=CASE)
    services.add_message(session, role="user", content=question)
    run = services.get_run_with_events(run_harness(session, question, llm_provider="scripted").pk)
    return run, RoadmapPayload.model_validate(run.output["roadmap"])


def test_case2_finishes_and_passes_check4(run_and_payload):
    """The run ends 'done' with every claim labeled and traceable."""
    run, _ = run_and_payload
    assert run.status == Run.Status.DONE
    assert run.output["notes"]["assumptions"]["A8"].startswith("No bills uploaded")


def test_case2_flags_the_missing_intake_fields(run_and_payload):
    """No bills and no roof replacement year are flagged, not invented."""
    run, _ = run_and_payload
    flags = run.output["notes"]["flags"]
    assert "missing_field:annual_kwh" in flags
    assert "missing_field:roof_replaced_year" in flags
    assert "missing_field:budget_year" in flags
    assert "missing_field:budget_type" in flags


def test_case2_baseline_is_a_low_confidence_assumption(run_and_payload):
    """With no bills, the baseline use is an ASSUMPTION with low confidence (A8)."""
    _, payload = run_and_payload
    baseline = [c for s in payload.sections for c in s.claims if c.assumption_id == "A8"]
    assert baseline and all(c.label == "ASSUMPTION" and c.confidence == "low" for c in baseline)


def test_case2_shows_the_conflict_and_leaves_closed_program_out_of_net_cost(run_and_payload):
    """The stale 'open' vs live 'closed' conflict is shown, and the closed program is never counted."""
    run, payload = run_and_payload
    assert "cached_live_conflict" in run.output["notes"]["flags"]
    section_7 = next(s for s in payload.sections if s.section_id == "7")
    text = " ".join(c.text.lower() for c in section_7.claims)
    assert "120 days" in text and "closed" in text and "left out of net cost" in text


def test_case2_puts_the_roof_survey_early_and_covers_every_number(run_and_payload):
    """The roof survey is in the first phases (before solar), and 100% of numbers are covered."""
    _, payload = run_and_payload
    roadmap = next(s for s in payload.sections if s.section_id == "8")
    survey_index = next(i for i, c in enumerate(roadmap.claims) if "roof condition survey" in c.text.lower())
    solar_index = next(i for i, c in enumerate(roadmap.claims) if "solar design" in c.text.lower())
    assert survey_index < solar_index
    assert check_coverage(payload).complete


def test_case2_is_listed_for_the_dev_landing_page(api_client):
    """The landing page lists the new case so it can be run from the browser."""
    ids = [item["id"] for item in api_client.get("/api/dev/fixtures").json()["fixtures"]]
    assert CASE in ids


def test_case2_upsert_cache_called_for_stale_incentive(run_and_payload):
    """v4: the agent saves the refreshed 'closed' status via upsert_reference_cache."""
    run, _ = run_and_payload
    events = list(run.events.order_by("seq"))
    upsert_calls = [
        e for e in events if e.kind == "tool_call" and e.payload.get("tool") == "upsert_reference_cache"
    ]
    assert len(upsert_calls) >= 1
    upsert_input = upsert_calls[0].payload.get("input", {})
    assert upsert_input.get("payload", {}).get("status") == "closed"


def test_case2_cache_rollback_restores_previous():
    """v4 goalpost: rolling back one cache record restores the previous version."""
    from tools.cache import get_reference_cache

    cache = get_reference_cache()
    record_id = "incentive:nyserda-school-solar-rollback"
    cache.put(
        record_id,
        {"name": "NYSERDA school solar program (fictional stand-in)", "status": "open"},
        source_url="https://example.test/fictional/case2/incentives",
        retrieved_at="2026-06-03T12:00:00Z",
    )
    cache.put(
        record_id,
        {"name": "NYSERDA school solar program (fictional stand-in)", "status": "closed"},
        source_url="https://example.test/fictional/case2/incentives",
        retrieved_at="2026-10-01T12:00:00Z",
    )
    assert cache.get(record_id)["status"] == "closed"
    rolled = cache.rollback(record_id)
    assert rolled is not None
    assert rolled["data"]["status"] == "open"
    assert cache.get(record_id)["status"] == "open"


def test_case2_nothing_from_user_or_model_saved(run_and_payload):
    """v4 goalpost: only approved-source data ends up in the cache."""
    from core.models import CacheRecord
    from tools.approved_sources import is_approved_source

    for record in CacheRecord.objects.all():
        assert is_approved_source(record.source_url), (
            f"Cache record {record.record_id} has unapproved source: {record.source_url}"
        )

