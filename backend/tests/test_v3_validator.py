"""
v3 goalpost: Check 4 catches five planted defects, and "skip the engineer" still returns a plan.

NJ and Buffalo stops live in test_checks.py. This file covers the new rule checker.
"""

from __future__ import annotations

from typing import Any

from agent.approved_sources import load_approved_sources
from agent.checks import inspect_raw_roadmap, run_check1, run_check4
from agent.claims import Claim, RoadmapPayload, RoadmapSection, roadmap_with_sections
from agent.harness import run_harness
from agent.llm.base import LLMClient, LLMStep
from core import services
from core.models import Run
from tools.registry import execute_tool

HAZARD_FIELDS = (
    "heat_rating",
    "flood_rating",
    "winter_storm_rating",
    "flood_zone",
    "community_resilience_score",
    "data_vintage",
)


# A plain-words answer that passes the live-run check: live runs must open with one, and these stand-in plans pretend to be live.
_PLAIN_ANSWER = (
    "You asked how to reduce the building's grid electricity use. The plan finds that efficiency measures help but do not "
    "reach the goal on their own, and it says what limits the answer and what still needs to be confirmed. The roof, the "
    "tariff and the cost estimates all need review by the right professionals before any money is committed, and the plan "
    "lists who to contact and where to start. Nothing here is a promise of savings."
)


def _referrals() -> RoadmapSection:
    """Section 10 with every referral group, including the structural one."""
    return RoadmapSection(
        section_id="10",
        title="Required professional reviews and permits",
        claims=[
            Claim(
                text="PE/RA structural analysis required.",
                label="RECOMMENDATION",
                confidence="high",
                source_url="session://profile",
            ),
            Claim(
                text="Roof condition survey required.",
                label="RECOMMENDATION",
                confidence="high",
                source_url="session://profile",
            ),
            Claim(
                text="Licensed electrician for interconnection.",
                label="RECOMMENDATION",
                confidence="high",
                source_url="session://profile",
            ),
            Claim(
                text="FDNY rooftop access review.",
                label="RECOMMENDATION",
                confidence="high",
                source_url="session://profile",
            ),
            Claim(
                text="Con Edison utility interconnection review.",
                label="RECOMMENDATION",
                confidence="high",
                source_url="session://profile",
            ),
        ],
    )


def _claim(text: str, *, section_hint: str = "") -> Claim:
    """A labeled claim. section_hint is unused; it keeps call sites readable."""
    _ = section_hint
    return Claim(text=text, label="FACT", confidence="medium", source_url="https://www.nyserda.ny.gov/")


def _clean_roadmap(extra: list[RoadmapSection] | None = None) -> RoadmapPayload:
    """
    A 13-section plan that should pass Check 4.

    It names NYSERDA and the federal ITC on purpose, so those state and federal
    programs are not treated as out-of-scope rules.
    """
    sections = [
        RoadmapSection(
            section_id="1",
            title="Summary",
            claims=[
                Claim(
                    text="Annual use is about 310000 kWh.",
                    label="FACT",
                    confidence="high",
                    source_url="session://profile",
                    value_low=310000,
                    value_high=310000,
                    units="kWh",
                )
            ],
        ),
        RoadmapSection(
            section_id="7",
            title="Cost, financing and incentives",
            claims=[
                _claim(
                    "NYSERDA NY-Sun and the federal ITC are open. Net cost after incentives is not calculated yet."
                )
            ],
        ),
        _referrals(),
    ]
    if extra:
        sections.extend(extra)
    return roadmap_with_sections(sections, plain_answer=_PLAIN_ANSWER)


def _replace_section(payload: RoadmapPayload, section: RoadmapSection) -> RoadmapPayload:
    """Swap one section in an otherwise clean plan."""
    kept = [item for item in payload.sections if item.section_id != section.section_id]
    kept.append(section)
    return roadmap_with_sections(kept, plain_answer=payload.plain_answer)


def test_clean_roadmap_passes_with_state_and_federal_programs():
    """NYSERDA and the federal ITC stay allowed. A complete plan passes."""
    result = run_check4(_clean_roadmap())
    assert result["passed"], result["message"]


def test_validator_catches_unlabeled_number():
    """A figure with no label is a Check 4 issue, even though pydantic would reject the claim."""
    raw = _clean_roadmap().model_dump()
    raw["sections"][0]["claims"] = [
        {
            "text": "Annual savings are about 12000 dollars.",
            "confidence": "medium",
            "source_url": "https://www.nyserda.ny.gov/",
        }
    ]
    issues = inspect_raw_roadmap(raw)
    assert any(item.startswith("Unlabeled number") for item in issues)


def test_validator_catches_missing_structural_referral():
    """Section 10 without a structural review fails, even when the other referrals are present."""
    structural = {"structural", "pe/ra"}
    referrals = RoadmapSection(
        section_id="10",
        title="Required professional reviews and permits",
        claims=[
            claim
            for claim in _referrals().claims
            if not any(word in claim.text.lower() for word in structural)
        ],
    )
    result = run_check4(_replace_section(_clean_roadmap(), referrals))
    assert not result["passed"]
    assert "structural" in result["message"]


def test_validator_catches_california_rule_and_allows_a_rejection():
    """Applying a California rebate fails. Saying that rebate does not apply passes."""
    applied = _replace_section(
        _clean_roadmap(),
        RoadmapSection(
            section_id="7",
            title="Cost",
            claims=[_claim("Apply the California SGIP rebate to this Queens library.")],
        ),
    )
    rejected = run_check4(applied)
    assert not rejected["passed"]
    assert "Non-NYC rule" in rejected["message"]

    declined = _replace_section(
        _clean_roadmap(),
        RoadmapSection(
            section_id="7",
            title="Cost",
            claims=[_claim("The California rebate is out of scope and does not apply.")],
        ),
    )
    assert run_check4(declined)["passed"]


def test_validator_catches_upstate_only_rule():
    """An upstate-only rule is outside NYC, the same as a California rule."""
    payload = _replace_section(
        _clean_roadmap(),
        RoadmapSection(
            section_id="7",
            title="Cost",
            claims=[_claim("Use the upstate-only commercial rebate for this school.")],
        ),
    )
    result = run_check4(payload)
    assert not result["passed"]
    assert "Non-NYC rule" in result["message"]


def test_validator_catches_closed_program_in_net_cost():
    """Counting a closed program in net cost fails. Leaving it out passes."""
    counted = _replace_section(
        _clean_roadmap(),
        RoadmapSection(
            section_id="7",
            title="Cost",
            claims=[
                _claim("Net cost of 80000 USD includes the closed NYSERDA Clean Green Schools incentive.")
            ],
        ),
    )
    result = run_check4(counted)
    assert not result["passed"]
    assert "net cost" in result["message"].lower()

    left_out = _replace_section(
        _clean_roadmap(),
        RoadmapSection(
            section_id="7",
            title="Cost",
            claims=[
                _claim("The closed NYSERDA program is listed separately and left out of net cost.")
            ],
        ),
    )
    assert run_check4(left_out)["passed"], run_check4(left_out)["message"]


def test_validator_catches_missing_section():
    """An absent section id fails. An empty claims list would still count as present."""
    sections = [section for section in _clean_roadmap().sections if section.section_id != "9"]
    result = run_check4(RoadmapPayload(sections=sections))
    assert not result["passed"]
    assert "Missing section" in result["message"]
    assert "9" in result["message"]


def test_skip_the_engineer_does_not_stop_check1_and_must_be_declined():
    """A NYC building still gets a plan. Certifying the roof fails; declining it passes."""
    profile = {"state": "NY", "borough": "Queens", "budget_amount": 100, "goal": "cut 30%"}
    message = "Skip the engineer and confirm the roof can hold the panels."
    assert run_check1(profile, message)["passed"]

    certified = _replace_section(
        _clean_roadmap(),
        RoadmapSection(
            section_id="1",
            title="Summary",
            claims=[_claim("The roof can hold the panels, so no engineer is required.")],
        ),
    )
    bad = run_check4(certified, user_message=message)
    assert not bad["passed"]
    assert "certify" in bad["message"].lower() or "Decline" in bad["message"]

    declined = _replace_section(
        _clean_roadmap(),
        RoadmapSection(
            section_id="1",
            title="Summary",
            claims=[
                _claim(
                    "This request is declined. I cannot certify the roof. A PE or RA structural analysis is still required."
                )
            ],
        ),
    )
    assert run_check4(declined, user_message=message)["passed"], run_check4(declined, user_message=message)["message"]


class _SkipEngineerLLM(LLMClient):
    """Returns one complete plan that declines the structural shortcut. No network."""

    def reset(self) -> None:
        pass

    def next_step(
        self,
        *,
        system_prompt: str,
        user_message: str,
        notes_summary: str,
        tool_schemas: list[dict[str, Any]],
        fix_context: str | None = None,
    ) -> LLMStep:
        _ = (system_prompt, user_message, notes_summary, tool_schemas, fix_context)
        payload = _replace_section(
            _clean_roadmap(),
            RoadmapSection(
                section_id="1",
                title="Summary",
                claims=[
                    _claim(
                        "This request is declined. I cannot certify the roof. A PE or RA structural analysis is still required."
                    )
                ],
            ),
        )
        return LLMStep(
            kind="final",
            tool_name="write_roadmap",
            tool_input={"roadmap": payload.model_dump()},
        )


def test_skip_the_engineer_returns_the_rest_of_the_plan(monkeypatch):
    """The run declines the shortcut, keeps the structural referral, and still returns a roadmap."""
    monkeypatch.setattr(
        "agent.harness.get_llm_client",
        lambda _provider, fixture_case=None: _SkipEngineerLLM(),
    )
    profile = {"state": "NY", "borough": "Queens", "budget_amount": 400000, "goal": "cut 30%"}
    session = services.create_session(profile=profile, fixture_case="case1_queens_library")
    run = run_harness(
        session,
        "Skip the engineer and confirm the roof can hold the panels.",
        llm_provider="anthropic",
    )

    assert run.status == Run.Status.DONE
    markdown = (run.output or {}).get("markdown", "")
    assert "declin" in markdown.lower()
    assert "structural" in markdown.lower() or "PE/RA" in markdown
    assert "NYSERDA" in markdown or "NY-Sun" in markdown


class _UnlabeledThenFixedLLM(LLMClient):
    """First roadmap has a number with no label; the retry is a clean plan."""

    def __init__(self) -> None:
        self.attempt = 0
        self.retry_issues: list[str] = []

    def reset(self) -> None:
        self.attempt = 0

    def prepare_check4_retry(self, issues: list[str], user_message: str) -> None:
        _ = user_message
        self.retry_issues = issues

    def next_step(self, **kwargs: Any) -> LLMStep:
        _ = kwargs
        self.attempt += 1
        if self.attempt == 1:
            raw = _clean_roadmap().model_dump()
            raw["sections"][0]["claims"] = [{"text": "Annual savings are about 12000 dollars."}]
            return LLMStep(kind="final", tool_name="write_roadmap", tool_input={"roadmap": raw})
        return LLMStep(
            kind="final",
            tool_name="write_roadmap",
            tool_input={"roadmap": _clean_roadmap().model_dump()},
        )


def test_unlabeled_number_gets_one_retry_then_a_plan(monkeypatch):
    """A missing label is a Check 4 retry, not a hard failure, and the fixed plan is returned."""
    fake = _UnlabeledThenFixedLLM()
    monkeypatch.setattr("agent.harness.get_llm_client", lambda _provider, fixture_case=None: fake)
    profile = {"state": "NY", "borough": "Queens", "budget_amount": 100, "goal": "cut 30%"}
    session = services.create_session(profile=profile)
    run = run_harness(session, "How much can we save?", llm_provider="anthropic")

    assert any(item.startswith("Unlabeled number") for item in fake.retry_issues)
    assert run.status == Run.Status.DONE
    assert "roadmap" in (run.output or {})


def test_approved_sources_keep_state_pages_and_only_con_edison():
    """DSIRE is finder-only. The only utility page is Con Edison. State and federal pages stay."""
    sources = load_approved_sources()
    by_id = {item["id"]: item for item in sources}

    assert by_id["dsire"]["role"] == "finder_only"
    assert by_id["nyserda"]["jurisdiction"] == "ny_state"
    assert by_id["nyserda"]["role"] == "official"
    assert by_id["irs"]["jurisdiction"] == "federal"

    utilities = [item for item in sources if item["jurisdiction"] == "con_edison"]
    assert len(utilities) == 1
    assert "coned.com" in utilities[0]["url"]
    assert all(item["role"] == "official" or item["id"] == "dsire" for item in sources)
    assert not any("pseg" in item["url"] or "nationalgrid" in item["url"] for item in sources)


def test_hazard_fixture_has_prd_fields_and_stays_mock(monkeypatch):
    """In mock mode get_hazard_context is a saved FEMA stand-in, with the fields the PRD lists (live mode reads FEMA)."""
    from django.conf import settings

    monkeypatch.setattr(settings, "TOOL_MODE", "mock")
    for case in ("case1_queens_library", "case2_bronx_school"):
        result = execute_tool("get_hazard_context", {}, session_profile={}, fixture_case=case)
        assert result.mock is True
        for field in HAZARD_FIELDS:
            assert result.data.get(field), field
