"""
Tests for the fixes found in the first run with the real Claude (see reference notes, "v1 live test review").

Nothing here calls the network or spends API credits: the Anthropic SDK is replaced by a small fake,
and the harness is driven by a stub model.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx
import pytest
from django.conf import settings

from agent import harness
from agent.harness import load_system_prompt, run_harness
from agent.llm import anthropic_client
from agent.llm.anthropic_client import AnthropicLLM
from agent.llm.base import LLMCallError, LLMClient, LLMStep
from agent.notes import AgentNotes
from core import services
from core.models import Run
from tools.base import ToolResult
from tools.cache import is_stale_for_tool
from tools.calculate import CalculateInput, run_calculate
from tools.registry import TOOL_SPECS

CASE = "case1_queens_library"


# ---------------------------------------------------------------- fake Anthropic SDK


class _FakeMessages:
    """Stands in for client.messages: records each request and returns (or raises) a canned outcome."""

    def __init__(self, outcome: Any, calls: list[dict[str, Any]]) -> None:
        self._outcome = outcome
        self._calls = calls

    def create(self, **kwargs: Any) -> Any:
        """Record the request, then raise the canned error or return the canned response."""
        self._calls.append(kwargs)
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


def _install_fake_sdk(monkeypatch: pytest.MonkeyPatch, outcome: Any) -> list[dict[str, Any]]:
    """Replace anthropic.Anthropic with a fake that answers with outcome; returns the list of requests."""
    calls: list[dict[str, Any]] = []

    class FakeAnthropic:
        """Looks like anthropic.Anthropic(api_key=...) but only exposes the fake messages.create."""

        def __init__(self, api_key: str) -> None:
            self.messages = _FakeMessages(outcome, calls)

    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    return calls


def _tool_use(tool_id: str, name: str = "get_building_profile") -> SimpleNamespace:
    """A tool_use block as the SDK returns it."""
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input={})


def _reply(*blocks: SimpleNamespace, stop_reason: str = "tool_use") -> SimpleNamespace:
    """A Messages API reply holding the given content blocks."""
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason)


def _next_step(llm: AnthropicLLM) -> LLMStep:
    """Ask the client for one step with trivial inputs."""
    return llm.next_step(system_prompt="system", user_message="question", notes_summary="notes", tool_schemas=[])


def _http_error(cls: type[anthropic.APIStatusError], status: int) -> anthropic.APIStatusError:
    """Build an SDK status error (404, 401, ...) without any network call."""
    response = httpx.Response(status, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    return cls(message="boom", response=response, body=None)


# ---------------------------------------------------------------- Anthropic client


def test_default_model_is_current_and_overridable(monkeypatch):
    """The default is the current model, not the retired one, and ANTHROPIC_MODEL still overrides it."""
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    assert anthropic_client._model_id() == "claude-sonnet-5-5"
    monkeypatch.setenv("ANTHROPIC_MODEL", "some-other-model")
    assert anthropic_client._model_id() == "some-other-model"


def test_request_allows_long_answers_and_one_tool_per_turn(monkeypatch):
    """The request asks for room for a full roadmap and for at most one tool call per turn."""
    monkeypatch.delenv("ANTHROPIC_MAX_TOKENS", raising=False)
    calls = _install_fake_sdk(monkeypatch, _reply(_tool_use("t1")))
    _next_step(AnthropicLLM())
    assert calls[0]["max_tokens"] == 16000
    assert calls[0]["tool_choice"] == {"type": "auto", "disable_parallel_tool_use": True}


def test_max_tokens_can_be_set_in_env_and_ignores_junk(monkeypatch):
    """ANTHROPIC_MAX_TOKENS raises the limit; a non-number falls back to the default."""
    monkeypatch.setenv("ANTHROPIC_MAX_TOKENS", "32000")
    assert anthropic_client._max_tokens() == 32000
    monkeypatch.setenv("ANTHROPIC_MAX_TOKENS", "lots")
    assert anthropic_client._max_tokens() == 16000


def test_cut_off_answer_is_reported_not_passed_on(monkeypatch):
    """A reply that stopped at the token limit raises a clear error instead of an empty roadmap."""
    _install_fake_sdk(monkeypatch, _reply(_tool_use("t1", "write_roadmap"), stop_reason="max_tokens"))
    with pytest.raises(LLMCallError, match="cut off"):
        _next_step(AnthropicLLM())


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_http_error(anthropic.NotFoundError, 404), "was not found"),
        (_http_error(anthropic.AuthenticationError, 401), "rejected the API key"),
        (_http_error(anthropic.RateLimitError, 429), "rate limit"),
        (_http_error(anthropic.InternalServerError, 500), "HTTP 500"),
        (anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com")), "Could not reach"),
    ],
)
def test_sdk_errors_become_readable_run_errors(monkeypatch, error, expected):
    """Wrong model, bad key, rate limit, outage and network trouble each become one plain sentence."""
    _install_fake_sdk(monkeypatch, error)
    with pytest.raises(LLMCallError, match=expected) as caught:
        _next_step(AnthropicLLM())
    assert "test-key" not in str(caught.value)


def test_extra_tool_calls_still_get_a_result(monkeypatch):
    """If the model sends two tool calls anyway, the second still gets a result so the next request is valid."""
    _install_fake_sdk(monkeypatch, _reply(_tool_use("t1"), _tool_use("t2", "get_utility_rates")))
    llm = AnthropicLLM()
    step = _next_step(llm)
    assert step.tool_use_id == "t1"

    llm.submit_tool_result("t1", "{}", "")
    results = llm._messages[-1]["content"]
    assert [r["tool_use_id"] for r in results] == ["t1", "t2"]
    assert results[1]["is_error"] is True


# ---------------------------------------------------------------- calculate


def test_calculate_names_the_missing_inputs():
    """A wrong input name gives a message that lists what is needed and what was sent, not a bare KeyError."""
    with pytest.raises(ValueError) as caught:
        run_calculate(CalculateInput(formula="C3", inputs={"annual_solar_kwh": 1000, "annual_kwh": 5000}))
    message = str(caught.value)
    assert "annual_use_kwh" in message  # what is missing
    assert "annual_solar_kwh, annual_use_kwh" in message  # what C3 needs
    assert "annual_kwh" in message  # what was sent


def test_calculate_description_lists_every_formulas_inputs():
    """The tool description the model sees names the exact inputs of C1 to C4."""
    description = TOOL_SPECS["calculate"].description
    for name in ("roof_area_sqft", "usable_roof_sqft", "annual_solar_kwh", "annual_use_kwh", "avg_rate_usd_per_kwh"):
        assert name in description


# ---------------------------------------------------------------- staleness and prompt


def test_tools_without_a_source_date_are_never_stale():
    """The intake and calculate have no retrieval date, so they are not stale; external data with none still is."""
    assert is_stale_for_tool("get_building_profile", "", "default") is False
    assert is_stale_for_tool("calculate", "", "default") is False
    assert is_stale_for_tool("get_solar_production", "", "solar_production") is True


def test_system_prompt_covers_live_data_ranges_and_flags():
    """The v1 prompt tells the model about one-tool-at-a-time, ranges, and the flags it must explain."""
    prompt = load_system_prompt()
    assert "one tool at a time" in prompt.lower()
    assert "annual_ac_kwh_low" in prompt
    for flag in (
        "intake_mismatch",
        "statewide_average_rate",
        "mock_data_in_live_run",
        "stale_data",
        "address_street_mismatch",
    ):
        assert flag in prompt


# ---------------------------------------------------------------- harness


class _StubLLM(LLMClient):
    """A model that follows a fixed list of steps and records every tool result the harness sends back."""

    def __init__(self, steps: list[LLMStep]) -> None:
        self._steps = list(steps)
        self.results: list[tuple[str, dict[str, Any]]] = []

    def reset(self) -> None:
        """Nothing to clear; the steps are fixed."""

    def submit_tool_result(self, tool_use_id: str, payload: str, notes_summary: str) -> None:
        """Remember what the harness sent back for this tool call."""
        self.results.append((tool_use_id, json.loads(payload)))

    def next_step(self, **_kwargs: Any) -> LLMStep:
        """Return the next canned step, or say the script is over."""
        return self._steps.pop(0) if self._steps else LLMStep(kind="exhausted", message="done")


def _profile() -> dict[str, Any]:
    """Dana's intake, enough to pass Check 1."""
    return {
        "state": "NY",
        "budget_amount": 400000,
        "goal": "Cut grid electricity 30% by 2030",
        "address": "41-17 Main Street",
        "borough": "Queens",
        "annual_kwh": 310000,
    }


def _run(monkeypatch: pytest.MonkeyPatch, steps: list[LLMStep], *, mode: str = "mock") -> tuple[Run, _StubLLM]:
    """Run the harness with the stub model and return the finished run plus the stub."""
    stub = _StubLLM(steps)
    monkeypatch.setattr(harness, "get_llm_client", lambda provider, fixture_case: stub)
    monkeypatch.setattr(settings, "TOOL_MODE", mode)
    session = services.create_session(profile=_profile(), fixture_case=CASE)
    run = run_harness(session, "How can we cut grid power 30%?", llm_provider="anthropic", tool_mode=mode)
    return services.get_run_with_events(run.pk), stub


def _calc(tool_use_id: str | None, inputs: dict[str, float]) -> LLMStep:
    """A calculate step for C3 with the given inputs."""
    return LLMStep(
        kind="tool",
        tool_name="calculate",
        tool_input={"formula": "C3", "inputs": inputs},
        tool_use_id=tool_use_id,
    )


def test_tool_error_goes_back_to_the_model_and_the_run_continues(monkeypatch):
    """A tool error is sent to the model as the tool result; the next call with fixed inputs then works."""
    wrong = {"annual_solar_kwh": 1000, "annual_kwh": 5000}
    right = {"annual_solar_kwh": 1000, "annual_use_kwh": 5000}
    run, stub = _run(monkeypatch, [_calc("t1", wrong), _calc("t2", right)])

    assert stub.results[0][0] == "t1"
    assert "annual_use_kwh" in stub.results[0][1]["error"]
    errors = [e for e in run.events.all() if e.kind == "error"]
    assert errors and errors[0].payload["will_retry"] is True
    calc_results = [e for e in run.events.all() if e.kind == "tool_result" and e.payload["tool"] == "calculate"]
    assert len(calc_results) == 1  # only the fixed call produced a result
    assert calc_results[0].payload["data"]["calc_id"] == "C3"


def test_tool_error_without_a_tool_use_id_is_logged_and_the_run_continues(monkeypatch):
    """
    v6: the scripted model cannot react to an error, but the run no longer stops there. The error is
    logged in readable words and the next scripted step still runs (it used to end the run as failed).
    """
    wrong = {"annual_solar_kwh": 1000, "annual_kwh": 5000}
    right = {"annual_solar_kwh": 1000, "annual_use_kwh": 5000}
    run, _ = _run(monkeypatch, [_calc(None, wrong), _calc(None, right)])

    errors = [e for e in run.events.all() if e.kind == "error" and e.payload.get("tool") == "calculate"]
    assert errors and "annual_use_kwh" in errors[0].payload["message"]
    calc_results = [e for e in run.events.all() if e.kind == "tool_result" and e.payload["tool"] == "calculate"]
    assert len(calc_results) == 1 and calc_results[0].payload["data"]["calc_id"] == "C3"


def test_intake_and_calculate_are_not_flagged_stale(monkeypatch):
    """get_building_profile and calculate no longer get a false stale_data flag."""
    steps = [
        LLMStep(kind="tool", tool_name="get_building_profile", tool_input={}, tool_use_id="t1"),
        _calc("t2", {"annual_solar_kwh": 1000, "annual_use_kwh": 5000}),
    ]
    run, _ = _run(monkeypatch, steps)
    for event in run.events.all():
        if event.kind == "tool_result":
            assert event.payload["stale"] is False
        if event.kind == "check3":
            assert "stale_data" not in (event.payload.get("flags") or [])


def test_mock_results_are_flagged_in_a_live_run_only(monkeypatch):
    """A tool that still answers from saved data is flagged mock_data_in_live_run in live mode, not in mock mode."""
    step = LLMStep(kind="tool", tool_name="get_hazard_context", tool_input={}, tool_use_id="t1")

    run, _ = _run(monkeypatch, [step], mode="live")
    live = [e for e in run.events.all() if e.kind == "tool_result"][0]
    assert live.payload["mock"] is True
    assert "mock_data_in_live_run" in live.payload["flags"]

    run, _ = _run(monkeypatch, [step], mode="mock")
    mocked = [e for e in run.events.all() if e.kind == "tool_result"][0]
    assert "mock_data_in_live_run" not in mocked.payload["flags"]


# ---------------------------------------------------------------- assumptions register fixes


def test_notes_auto_registers_tool_and_calculation_assumptions():
    """
    ISSUE:
    In live Anthropic runs, Check 4 rejected claims with:
    "Claim ASSUMPTION 'A1' not in notes assumptions register"
    because AgentNotes only populated assumptions from calculate calls with explicit assumption_ids.
    
    FIX:
    AgentNotes now auto-populates assumptions from tools:
    - get_solar_production (range_assumption -> A1)
    - calculate C1 (setback_factor -> A2)
    - calculate C2 (sqft_per_kw -> A3)
    - optimize_solar_storage (stand-in storage sizing -> A4)
    - mock incentive and hazard tools (A5, A6)
    """
    notes = AgentNotes()

    # 1. get_solar_production registers A1 from range_assumption
    solar_res = ToolResult(
        tool="get_solar_production",
        data={"annual_ac_kwh": 60000, "range_assumption": "ASSUMPTION: system losses 10%-18%"},
        source_url="https://developer.nlr.gov/docs/solar/pvwatts/v8/",
        retrieved_at="2026-10-15T00:00:00Z",
        dataset_version="pvwatts-v8",
        mock=False,
    )
    notes.record_tool_result("get_solar_production", solar_res)
    assert "A1" in notes.assumptions
    assert "system losses" in notes.assumptions["A1"]

    # 2. calculate C1 and C2 auto-populate A2 and A3
    c1_res = run_calculate(CalculateInput(formula="C1", inputs={"roof_area_sqft": 6000}))
    notes.record_tool_result("calculate", c1_res)
    assert "A2" in notes.assumptions
    assert "0.55" in notes.assumptions["A2"]

    c2_res = run_calculate(CalculateInput(formula="C2", inputs={"usable_roof_sqft": 3300}))
    notes.record_tool_result("calculate", c2_res)
    assert "A3" in notes.assumptions
    assert "66" in notes.assumptions["A3"]

    # 3. optimize_solar_storage registers A4
    reopt_res = ToolResult(
        tool="optimize_solar_storage",
        data={"notes": "Sized for 8 hours cooling center", "battery_kw": 120},
        source_url="https://example.test/fictional/reopt",
        retrieved_at="2026-10-15T00:00:00Z",
        dataset_version="reopt-v0",
        mock=True,
    )
    notes.record_tool_result("optimize_solar_storage", reopt_res)
    assert "A4" in notes.assumptions

    # 4. Working notes summary presents them to the LLM context
    summary = notes.summarize_for_llm()
    assert "Assumptions: A1:" in summary
    assert "A2:" in summary
    assert "A3:" in summary
    assert "A4:" in summary


def test_check4_passes_with_notes_auto_registered_assumptions():
    """Check 4 passes on an ASSUMPTION claim citing A1 from notes.assumptions."""
    from agent.checks import run_check4
    from agent.claims import Claim, RoadmapSection, roadmap_with_sections

    notes = AgentNotes()
    solar_res = ToolResult(
        tool="get_solar_production",
        data={"annual_ac_kwh": 60000, "range_assumption": "ASSUMPTION: system losses 10%-18%"},
        source_url="https://developer.nlr.gov/docs/solar/pvwatts/v8/",
        retrieved_at="2026-10-15T00:00:00Z",
        dataset_version="pvwatts-v8",
        mock=False,
    )
    notes.record_tool_result("get_solar_production", solar_res)

    payload = roadmap_with_sections([
        RoadmapSection(
            section_id="3",
            title="Assumptions",
            claims=[
                Claim(
                    text="Assumed loss band: system losses 10%-18%",
                    label="ASSUMPTION",
                    confidence="medium",
                    assumption_id="A1",
                )
            ],
        ),
        RoadmapSection(
            section_id="10",
            title="Referrals",
            claims=[
                Claim(
                    text=(
                        "Mandatory referrals: professional engineer structural PE/RA analysis, "
                        "roof survey and condition, licensed electrician, FDNY rooftop access, "
                        "and Con Edison utility interconnection."
                    ),
                    label="RECOMMENDATION",
                    confidence="high",
                    source_url="session://profile",
                )
            ],
        ),
    ])

    check_res = run_check4(payload, assumptions_register=notes.assumptions)
    assert check_res["passed"] is True, check_res.get("message")


def test_live_storage_does_not_become_an_assumption():
    """A real storage result is data, not a sample assumption. Only mock storage fills A4."""
    notes = AgentNotes()
    live = ToolResult(
        tool="optimize_solar_storage",
        data={"notes": "Live optimizer result", "battery_kw": 40},
        source_url="https://example.test/live-reopt",
        retrieved_at="2026-10-15T00:00:00Z",
        dataset_version="reopt-live",
        mock=False,
    )
    notes.record_tool_result("optimize_solar_storage", live)
    assert "A4" not in notes.assumptions


def test_repeated_calculations_stay_in_the_notes_summary():
    """Three C4 calls (low, high, central) all remain visible. The last one must not erase the range."""
    notes = AgentNotes()
    for kwh, rate in ((58976, 0.1981), (64809, 0.2418), (61894, 0.222)):
        result = run_calculate(
            CalculateInput(formula="C4", inputs={"annual_solar_kwh": kwh, "avg_rate_usd_per_kwh": rate})
        )
        notes.record_tool_result("calculate", result)

    assert len(notes.calculation_runs["C4"]) == 3
    summary = notes.summarize_for_llm()
    assert "11683" in summary
    assert "15670" in summary
    assert "13740" in summary


def test_mock_fixtures_do_not_share_the_solar_source_url():
    """Incentives, hazards, storage, rates, and building records each cite their own sample source."""
    from mocks.mock_mode import load_fixture

    solar = load_fixture(CASE, "get_solar_production").source_url
    assert "pvwatts" in solar
    others = [
        "optimize_solar_storage",
        "search_ny_incentives_and_rules",
        "get_hazard_context",
        "get_utility_rates",
        "lookup_ny_building_records",
    ]
    urls = [load_fixture(CASE, name).source_url for name in others]
    assert solar not in urls
    assert len(set(urls)) == len(urls)
    assert all("pvwatts" not in url for url in urls)


@pytest.mark.parametrize(
    ("address", "street"),
    [
        ("41-17 Main Street", "MAIN STREET"),
        ("41-24 KISSENA BOULEVARD", "KISSENA BOULEVARD"),
        ("10-20 Queens Boulevard", "QUEENS BOULEVARD"),  # starts with a place word
        ("55 Flushing Ave", "FLUSHING AVENUE"),  # short suffix is spelled out
        ("12 New York Avenue", "NEW YORK AVENUE"),
        ("41-17 Main Street, Flushing, NY, USA", "MAIN STREET"),  # trailing place names are dropped
        ("41-17 Main, Queens", "MAIN"),  # no suffix: stop at the place name
        ("25 St Marks Place", "ST MARKS PLACE"),  # a leading "St" is not a suffix
        ("", ""),
    ],
)
def test_street_name_keeps_streets_that_start_with_a_place_word(address, street):
    """The street-mismatch check compares street names; streets like Queens Boulevard must not come out empty."""
    from tools.live_records import _street_name

    assert _street_name(address) == street
