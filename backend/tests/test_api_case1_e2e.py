"""
HTTP API smoke test for case1 — session, profile, upload, message, roadmap download.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE_CSV = (
    Path(__file__).resolve().parents[1]
    / "mocks/fixtures/case1_queens_library/documents/bills_2025.csv"
)


@pytest.fixture(autouse=True)
def scripted_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("TOOL_MODE", "mock")
    from django.conf import settings

    settings.LLM_PROVIDER = "scripted"
    settings.TOOL_MODE = "mock"


def test_api_case1_flow(api_client):
    created = api_client.post("/api/sessions", json={"fixture_case": "case1_queens_library"})
    assert created.status_code == 200
    session_id = created.json()["id"]

    profile = json.loads(
        (Path(__file__).resolve().parents[1] / "mocks/fixtures/case1_queens_library/intake.json").read_text()
    )
    profile.pop("_comment", None)
    put = api_client.put(f"/api/sessions/{session_id}/profile", json={"profile": profile})
    assert put.status_code == 200

    with FIXTURE_CSV.open("rb") as fh:
        up = api_client.post(
            f"/api/sessions/{session_id}/documents",
            files={"file": ("bills_2025.csv", fh, "text/csv")},
        )
    assert up.status_code == 200
    assert up.json()["parsed_summary"].get("total_kwh") == 310000

    msg = api_client.post(
        f"/api/sessions/{session_id}/messages",
        json={"content": "How can we cut grid power 30% by 2030 on $400k?"},
    )
    assert msg.status_code == 200
    run_id = msg.json()["run"]["id"]
    assert msg.json()["run"]["status"] in ("done", "partial")

    run_get = api_client.get(f"/api/runs/{run_id}")
    assert run_get.status_code == 200
    assert len(run_get.json()["events"]) >= 5

    md = api_client.get(f"/api/runs/{run_id}/roadmap.md")
    assert md.status_code == 200
    assert "Professor Fritts" in md.text

    rd = api_client.get(f"/api/runs/{run_id}/roadmap.json")
    assert rd.status_code == 200
    assert "sections" in rd.json()
