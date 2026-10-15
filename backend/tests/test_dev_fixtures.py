"""
Dev fixture routes — the landing page lists cases and a scripted run ends with final.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def scripted_env(monkeypatch):
    """Keep this test off the network: scripted model, mock tools."""
    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("TOOL_MODE", "mock")
    from django.conf import settings

    settings.LLM_PROVIDER = "scripted"
    settings.TOOL_MODE = "mock"


def test_list_fixtures_includes_queens_library(api_client):
    response = api_client.get("/api/dev/fixtures")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["fixtures"]]
    assert "case1_queens_library" in ids


def test_run_fixture_ends_with_final_event(api_client):
    response = api_client.post("/api/dev/fixtures/case1_queens_library/run")
    assert response.status_code == 200
    run = response.json()["run"]
    assert run["events"], "expected a trace"
    last = run["events"][-1]
    assert last["kind"] == "final"
    assert last["payload"]["status"] == run["status"]


def test_run_unknown_fixture_is_404(api_client):
    response = api_client.post("/api/dev/fixtures/not_a_case/run")
    assert response.status_code == 404
