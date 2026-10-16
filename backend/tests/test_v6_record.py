"""
Tests for recording a finished run as a replayable case (v6).

A recording saves the tool calls, the tool answers and the final plan of one run, so it can be replayed for free
with the scripted model. These tests record a saved scripted run into a temporary folder and check that the replay
gives the same status, the same plan and the same tool answers. Nothing here calls the network or Claude.
"""

from __future__ import annotations

import json

import pytest
from django.conf import settings

from agent.evals import run_eval_case
from agent.harness import run_harness
from agent.record import RecordError, record_run
from core import services
from core.models import Run
from mocks.catalog import load_case


@pytest.fixture(autouse=True)
def mock_tools(monkeypatch):
    """Scripted model and mock tools for every test here."""
    monkeypatch.setattr(settings, "TOOL_MODE", "mock")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "scripted")


def _source_run(case: str = "case8_flood_zone") -> Run:
    """Run a saved eval case once and return its stored run, as the thing to record."""
    assert run_eval_case(case).passed
    return Run.objects.order_by("-pk").first()


def _point_fixtures_at(monkeypatch, root) -> None:
    """Make the loaders read cases from this folder instead of the repo's fixtures."""
    monkeypatch.setattr("mocks.catalog.FIXTURES_ROOT", root)
    monkeypatch.setattr("mocks.mock_mode.FIXTURES_ROOT", root)
    monkeypatch.setattr("agent.llm.scripted.FIXTURES_ROOT", root)


def test_a_recording_writes_the_script_the_intake_and_the_outside_tool_answers(tmp_path):
    """The case folder gets the script, the intake with its question, and a file for each outside tool the run used."""
    run = _source_run()
    summary = record_run(run, "rec_flood", root=tmp_path)
    folder = tmp_path / "rec_flood"
    steps = json.loads((folder / "scripted_llm.json").read_text(encoding="utf-8"))["steps"]
    assert steps[0]["type"] == "think" and steps[-1]["type"] == "final" and steps[-1]["name"] == "write_roadmap"
    assert [s["name"] for s in steps if s["type"] == "tool"][:2] == ["get_building_profile", "lookup_ny_building_records"]
    intake = json.loads((folder / "intake.json").read_text(encoding="utf-8"))
    assert intake["building_name"] and intake["question"]
    assert "get_hazard_context.json" in summary["written"] and "get_solar_production.json" in summary["written"]
    # Plain-code tools are not saved: they run again.
    assert not (folder / "calculate.json").exists() and not (folder / "run_financial_model.json").exists()


def test_the_replay_gives_the_same_status_plan_and_tool_answers(tmp_path, monkeypatch):
    """Replaying the recording reproduces the original run: same status, same plan, same hazard answer."""
    original = _source_run()
    record_record = record_run(original, "rec_flood", root=tmp_path)
    assert record_record["warnings"] == []
    _point_fixtures_at(monkeypatch, tmp_path)

    profile, question = load_case("rec_flood")
    session = services.create_session(profile=profile, fixture_case="rec_flood")
    services.add_message(session, role="user", content=question)
    replay = services.get_run_with_events(run_harness(session, question, llm_provider="scripted", tool_mode="mock").pk)

    assert replay.status == original.status
    assert replay.output["roadmap"] == original.output["roadmap"]
    hazard = [e.payload for e in replay.events.all() if e.kind == "tool_result" and e.payload["tool"] == "get_hazard_context"]
    assert hazard and hazard[0]["data"]["flood_zone"] == "AE"


def test_existing_files_are_kept_unless_overwrite_is_asked_for(tmp_path):
    """A hand-made data file or intake is not replaced by accident; overwrite replaces it."""
    run = _source_run()
    folder = tmp_path / "rec_flood"
    folder.mkdir()
    (folder / "get_hazard_context.json").write_text('{"hand": "made"}', encoding="utf-8")
    (folder / "intake.json").write_text('{"building_name": "mine"}', encoding="utf-8")

    kept = record_run(run, "rec_flood", root=tmp_path)
    assert "get_hazard_context.json" in kept["kept"] and "intake.json" in kept["kept"]
    assert json.loads((folder / "intake.json").read_text(encoding="utf-8")) == {"building_name": "mine"}

    forced = record_run(run, "rec_flood", root=tmp_path, overwrite=True)
    assert "get_hazard_context.json" in forced["written"]
    assert json.loads((folder / "get_hazard_context.json").read_text(encoding="utf-8"))["tool"] == "get_hazard_context"


def test_a_run_with_no_plan_cannot_be_recorded(tmp_path):
    """A run that stopped before writing a plan (for example, out of scope) has nothing to record, and says so."""
    profile, question = load_case("case4_upstate_buffalo")
    session = services.create_session(profile=profile, fixture_case="case4_upstate_buffalo")
    run = run_harness(session, question, llm_provider="scripted")
    with pytest.raises(RecordError, match="no plan"):
        record_run(run, "rec_none", root=tmp_path)
