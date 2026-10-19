"""
Code-enforced safety checks 1–4 from the agent-flow diagram.

Each returns a dict logged as a RunEvent; passed=False stops or flags the run as documented.
"""

from __future__ import annotations

import re
from typing import Any

from agent.claims import (
    PROMISE_WORDS,
    SECTION_TITLES,
    Claim,
    RoadmapPayload,
    RoadmapSection,
)
from agent.limits import RunLimits, tool_call_limit, tool_retry_limit
from agent.notes import AgentNotes
from tools.base import ToolResult
from tools.cache import is_stale_for_tool
from tools.registry import get_tool_spec, list_tool_names, validate_tool_input

# The hidden-instruction phrases live in tools/injection.py so the tools can use them too.
# Re-exported here because older tests import HIDDEN_INSTRUCTION_PATTERNS from this module.
from tools.injection import HIDDEN_INSTRUCTION_PATTERNS, find_hidden_instructions  # noqa: E402,F401

NY_STATE_CODES = {"NY", "NEW YORK", "NYC", "NEW YORK CITY"}

# Scope is NYC only (decided Oct 15, 2026): the five boroughs. Each borough can also arrive under its
# county name (Kings = Brooklyn, Richmond = Staten Island, New York = Manhattan), so those map here.
# Anything not in this table, such as Buffalo or Erie County, is out of scope.
NYC_BOROUGH_NAMES: dict[str, str] = {
    "manhattan": "Manhattan",
    "new york": "Manhattan",
    "brooklyn": "Brooklyn",
    "kings": "Brooklyn",
    "queens": "Queens",
    "bronx": "Bronx",
    "the bronx": "Bronx",
    "staten island": "Staten Island",
    "richmond": "Staten Island",
}


def normalize_borough(raw: str | None) -> str | None:
    """
    Turn what the user typed into one of the five borough names, or None if it is not a NYC borough.

    Ignores case, extra spaces and filler words ("Borough of", "County"), so "Kings County" and
    "borough of queens" both work. To support another spelling, add it to NYC_BOROUGH_NAMES.
    """
    text = re.sub(r"\b(borough of|county)\b", " ", (raw or "").lower())
    text = re.sub(r"\s+", " ", text).strip()
    return NYC_BOROUGH_NAMES.get(text)


class CheckResult(dict):
    """Structured check outcome — use like a dict with keys passed, code, message, details."""

    @staticmethod
    def ok(code: str, message: str = "ok", **details: Any) -> CheckResult:
        return CheckResult(passed=True, code=code, message=message, details=details)

    @staticmethod
    def fail(code: str, message: str, **details: Any) -> CheckResult:
        return CheckResult(passed=False, code=code, message=message, details=details)


def _profile_state(profile: dict[str, Any]) -> str:
    raw = (profile.get("state") or profile.get("State") or "").strip().upper()
    return raw


def _has_budget(profile: dict[str, Any]) -> bool:
    budget = profile.get("budget_amount") or profile.get("budget")
    return budget not in (None, "", 0)


def _has_goal(profile: dict[str, Any]) -> bool:
    goal = profile.get("goal") or profile.get("energy_goal") or profile.get("goal_percent")
    return bool(str(goal or "").strip())


def run_check1(profile: dict[str, Any], user_message: str) -> CheckResult:
    """
    Start gate: NYC only (five boroughs); budget and goal required or ask once (needs_input).

    A building in another state, or in New York State outside the five boroughs (Buffalo, Erie
    County, Long Island), stops as out_of_scope. A missing borough, budget or goal gets one
    clarifying question. State programs still apply to NYC buildings; this only checks location.
    """
    state = _profile_state(profile)
    # The intake form calls this field "Borough" but older sessions may send it as "county".
    borough_text = str(profile.get("borough") or profile.get("county") or "").strip()
    out_of_scope_message = (
        "Professor Fritts supports New York City public buildings only "
        "(Manhattan, Brooklyn, Queens, the Bronx and Staten Island)."
    )

    # Another state entirely (NJ, CA, ...) stops at once.
    if state and state not in NY_STATE_CODES and "NEW YORK" not in state:
        return CheckResult.fail("out_of_scope", out_of_scope_message, stop_reason="out_of_scope")

    # A borough was given but it is not one of the five (for example Buffalo or Erie): stop at once.
    if borough_text and normalize_borough(borough_text) is None:
        return CheckResult.fail("out_of_scope", out_of_scope_message, stop_reason="out_of_scope")

    missing: list[str] = []
    if not state:
        missing.append("state (NY)")
    if not borough_text:
        missing.append("borough")
    if not _has_budget(profile):
        missing.append("capital budget")
    if not _has_goal(profile):
        missing.append("energy goal")

    if missing:
        question = (
            "To start your roadmap I need: "
            + ", ".join(missing)
            + ". Please add them to the intake form and send your question again."
        )
        return CheckResult.fail(
            "needs_input",
            question,
            stop_reason="needs_input",
            question=question,
        )

    return CheckResult.ok("check1_pass", "NYC building with borough, budget and goal present.")


def run_check2(
    tool_name: str,
    raw_input: dict[str, Any],
    limits: RunLimits,
    *,
    is_final_tool: bool = False,
    blocked_sources: set[str] | None = None,
) -> CheckResult:
    """
    Tool gate: registered tool, valid schema, under call/retry/time limits.

    Final tools write_roadmap / write_answer skip registry lookup when is_final_tool=True.
    blocked_sources (v6) holds pages ignored for hidden instructions this run; a cache write
    from one of them is refused here, before the write tool even runs.
    """
    if limits.timeout_exceeded():
        return CheckResult.fail("timeout", "Run exceeded the time limit.")

    if is_final_tool:
        if tool_name in ("write_roadmap", "write_answer"):
            return CheckResult.ok("check2_pass", "Final structured output tool approved.")
        return CheckResult.fail("unknown_tool", f"Unknown final tool {tool_name!r}.")

    if tool_name not in list_tool_names():
        return CheckResult.fail("unknown_tool", f"Tool {tool_name!r} is not registered in v0.")

    if limits.tool_call_count >= tool_call_limit():
        return CheckResult.fail("tool_limit", f"Tool call limit ({tool_call_limit()}) reached.")

    failed = limits.failed_attempts_by_tool.get(tool_name, 0)
    if failed >= tool_retry_limit():
        return CheckResult.fail(
            "retry_limit",
            f"Retry limit ({tool_retry_limit()}) reached for tool {tool_name!r}.",
        )

    try:
        validate_tool_input(tool_name, raw_input)
    except Exception as exc:  # pydantic ValidationError
        return CheckResult.fail("invalid_input", f"Invalid input for {tool_name}: {exc}")

    if tool_name == "upsert_reference_cache" and blocked_sources:
        if str((raw_input or {}).get("source_url") or "") in blocked_sources:
            return CheckResult.fail(
                "quarantined_source",
                "That page was ignored for hidden instructions; nothing from it is saved.",
            )

    return CheckResult.ok("check2_pass", f"Tool {tool_name} approved.")


def run_check3(result: ToolResult, *, freshness_kind: str = "default") -> CheckResult:
    """
    Answer gate: provenance fields, stale flag, injection pattern scan on serialized data.

    Results are treated as data only. Any hidden-instruction match adds a flag and sets
    details.quarantine, and the harness then withholds the result's data from the model (v6).
    """
    missing = []
    if not result.source_url:
        missing.append("source_url")
    if not result.retrieved_at and result.tool != "get_building_profile" and result.tool != "calculate":
        missing.append("retrieved_at")
    if not result.dataset_version and result.tool != "get_building_profile":
        missing.append("dataset_version")

    flags: list[str] = list(result.flags)
    hidden = find_hidden_instructions(result.data)
    if hidden and "hidden_instruction_pattern" not in flags:
        flags.append("hidden_instruction_pattern")

    stale = result.stale or is_stale_for_tool(result.tool, result.retrieved_at, freshness_kind)
    if stale and "stale_data" not in flags:
        flags.append("stale_data")

    if missing:
        return CheckResult.fail(
            "missing_provenance",
            f"Tool result missing: {', '.join(missing)}",
            missing=missing,
            flags=flags,
        )

    if hidden:
        return CheckResult.ok(
            "check3_quarantine",
            "Hidden instructions found in the result; it is ignored and not passed to the model.",
            stale=stale,
            flags=flags,
            quarantine=True,
            hidden_instructions=hidden,
        )

    return CheckResult.ok(
        "check3_pass",
        "Provenance present; result wrapped as data.",
        stale=stale,
        flags=flags,
    )


# A digit in the claim text, or a value range, counts as a number that needs a label,
# a confidence, and an id. Dates and dollar amounts count too.
_HAS_DIGIT = re.compile(r"\d")

# Rules and rebates that do not apply to an NYC building. New York State programs
# (NYSERDA, NY-Sun) and federal programs are intentionally not in this list.
_NON_NYC_RULE = re.compile(
    r"\b(california|calif\.|ca rebate|sgip|upstate(?:-only)?|erie county|buffalo|new jersey|nj rebate)\b",
    re.I,
)

# The claim is naming the outside rule in order to reject it, not to apply it.
_RULE_EXCLUDED = re.compile(
    r"out of scope|does not apply|do not apply|doesn't apply|not applicable|"
    r"excluded|leave out|left out|not included|cannot use|can't use|do not use|don't use",
    re.I,
)

_CLOSED_OR_UNCERTAIN = re.compile(r"\b(closed|uncertain)\b", re.I)
_PROGRAM_WORD = re.compile(r"\b(program|incentive|rebate|credit)\b", re.I)
_NET_COST = re.compile(r"net cost", re.I)
_LEFT_OUT_OF_NET = re.compile(
    r"left out|leave out|excluded|listed separately|not included|not counted|"
    r"do not count|not part of",
    re.I,
)

# The user is asking the agent to skip a structural review or to certify the roof.
_SKIP_ENGINEER = re.compile(
    r"skip the engineer|skip the structural|skip (?:a |the )?professional review|"
    r"don'?t need (?:an |a )?engineer|do not need (?:an |a )?engineer|"
    r"without (?:an |a )?engineer|confirm the roof can hold|roof can hold the panels",
    re.I,
)
_CERTIFIES_ROOF = re.compile(
    r"roof can hold|roof can carry|confirmed the roof|"
    r"structure (?:is|can) (?:adequate|sound|carry)|"
    r"panels? (?:will|can) be (?:supported|carried)",
    re.I,
)
# "Cannot certify that the roof can carry the panels" refuses to certify; it must not count as
# certifying. The refusal and the clause it governs (up to the next , ; or .) are removed before
# _CERTIFIES_ROOF runs. Found in a live case 3 run: the model copied Check 4's own fix text and was
# rejected again. "I confirm the roof can hold the panels" still fails.
_NEGATED_CERTIFY = re.compile(
    r"\b(?:cannot|can't|can not|will not|won't|do not|don't|never|unable to|not able to)\s+"
    r"(?:certify|confirm|verify|guarantee|promise|say|state)\b[^.;,]*",
    re.I,
)
_DECLINES_SKIP = re.compile(
    r"\bdeclin\w*|cannot skip|can'?t skip|will not confirm|cannot confirm|"
    r"must not skip|do not certify|cannot certify",
    re.I,
)

_LABELS = {"FACT", "ESTIMATE", "ASSUMPTION", "RECOMMENDATION"}


def _claim_has_number(text: str, value_low: Any) -> bool:
    """True when the claim states a figure, either in its range or in its words."""
    return value_low is not None or bool(_HAS_DIGIT.search(text or ""))


def _claim_has_id(source_url: Any, calc_id: Any, assumption_id: Any) -> bool:
    """True when the claim points at a source, a calculation, or an assumption id."""
    return bool(source_url or calc_id or assumption_id)


def _non_nyc_rule_issues(section_id: str, text: str) -> list[str]:
    """
    Flag a claim that applies a rule from outside NYC.

    A sentence that says the outside rule does not apply is allowed. NYSERDA and
    federal programs do not match the pattern, so they stay in the plan.
    """
    if _NON_NYC_RULE.search(text) and not _RULE_EXCLUDED.search(text):
        return [f"Non-NYC rule in section {section_id}: {text[:80]}"]
    return []


def _closed_in_net_cost_issue(section_id: str, text: str) -> str | None:
    """
    Flag a section 7 claim that counts a closed or uncertain program in net cost.

    Saying the program is left out, excluded, or listed separately is the passing case.
    Other sections may mention a closed program without this check.
    """
    if section_id not in ("7", "section_7"):
        return None
    if not _PROGRAM_WORD.search(text):
        return None
    if not _CLOSED_OR_UNCERTAIN.search(text) or not _NET_COST.search(text):
        return None
    if _LEFT_OUT_OF_NET.search(text):
        return None
    return f"Closed or uncertain program counted in net cost: {text[:80]}"


def _missing_section_issues(section_ids: set[str]) -> list[str]:
    """Name every PRD section id the roadmap left out. An empty claims list still counts."""
    missing = [section_id for section_id in SECTION_TITLES if section_id not in section_ids]
    if not missing:
        return []
    return [f"Missing section(s): {', '.join(missing)}."]


def _skip_engineer_issues(user_message: str, combined_text: str) -> list[str]:
    """
    When the user asks to skip the engineer, the plan must decline and must not certify the roof.

    The structural referral itself is checked separately. This only looks at the request
    and the wording of the answer. The run still continues with the rest of the plan.
    """
    if not user_message or not _SKIP_ENGINEER.search(user_message):
        return []
    issues: list[str] = []
    if _CERTIFIES_ROOF.search(_NEGATED_CERTIFY.sub(" ", combined_text)):
        issues.append(
            "Cannot certify that the roof can carry the panels. Decline the request and keep the structural referral."
        )
    if not _DECLINES_SKIP.search(combined_text):
        issues.append(
            "The user asked to skip the engineer. Decline that request and explain a PE or RA structural analysis is still required."
        )
    return issues


def inspect_raw_roadmap(raw: dict | None, *, user_message: str = "") -> list[str]:
    """
    Read a write_roadmap dict before pydantic so a missing label is a Check 4 issue.

    Pydantic rejects a claim with no label, and the harness used to stop the whole run.
    Call this when validation fails. The issues go through the one-retry path instead.
    Pass the user message so a "skip the engineer" request is still checked.
    """
    if not isinstance(raw, dict):
        return ["Roadmap payload is missing."]
    sections = raw.get("sections")
    if not isinstance(sections, list):
        return ["Roadmap has no sections list."]

    issues: list[str] = []
    present: set[str] = set()
    texts: list[str] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("section_id") or "")
        present.add(section_id)
        for claim in section.get("claims") or []:
            if not isinstance(claim, dict):
                continue
            text = str(claim.get("text") or "")
            texts.append(text)
            if _claim_has_number(text, claim.get("value_low")) and (
                claim.get("label") not in _LABELS
                or not claim.get("confidence")
                or not _claim_has_id(claim.get("source_url"), claim.get("calc_id"), claim.get("assumption_id"))
            ):
                issues.append(f"Unlabeled number: {text[:80]}")
            issues.extend(_non_nyc_rule_issues(section_id, text))
            closed = _closed_in_net_cost_issue(section_id, text)
            if closed:
                issues.append(closed)
    issues.extend(_missing_section_issues(present))
    issues.extend(_skip_engineer_issues(user_message, " ".join(texts)))
    missing_referrals = _missing_referral_groups(salvage_roadmap(raw))
    if missing_referrals:
        issues.append(
            "Mandatory professional referrals are incomplete in section 10 ("
            + ", ".join(missing_referrals)
            + ")."
        )
    return issues


def salvage_roadmap(raw: dict | None) -> RoadmapPayload:
    """
    Keep every claim that still validates when the whole roadmap does not.

    A missing label fails pydantic for the entire write_roadmap call. The harness still
    needs a roadmap object so a partial plan can be returned after the one retry.
    Claims that fail validation are dropped; their problem is already listed in the issues.
    """
    sections: list[RoadmapSection] = []
    if not isinstance(raw, dict):
        return RoadmapPayload(sections=[])
    for section in raw.get("sections") or []:
        if not isinstance(section, dict):
            continue
        claims: list[Claim] = []
        for claim in section.get("claims") or []:
            if not isinstance(claim, dict):
                continue
            try:
                claims.append(Claim.model_validate(claim))
            except Exception:
                continue
        sections.append(
            RoadmapSection(
                section_id=str(section.get("section_id") or "?"),
                title=str(section.get("title") or "Untitled"),
                claims=claims,
            )
        )
    return RoadmapPayload(sections=sections)


def _claim_traceability_ok(claim: Claim, assumptions_register: dict[str, str]) -> tuple[bool, str | None]:
    """
    Return whether the claim meets Check 4 traceability and a short issue string if not.

    ASSUMPTION claims tie to the in-run assumptions register; other labels need source or calc.
    """
    if claim.label == "ASSUMPTION":
        aid = (claim.assumption_id or "").strip()
        if not aid:
            return False, "ASSUMPTION missing assumption_id"
        if aid not in assumptions_register:
            return False, f"ASSUMPTION {aid!r} not in notes assumptions register"
        return True, None
    if claim.label in ("FACT", "ESTIMATE", "RECOMMENDATION"):
        if claim.source_url or claim.calc_id:
            return True, None
        return False, "missing source_url or calc_id"
    return False, "invalid label"


def _collect_claims(payload: RoadmapPayload) -> list[Claim]:
    claims: list[Claim] = []
    for section in payload.sections:
        claims.extend(section.claims)
    return claims


def _missing_referral_groups(payload: RoadmapPayload) -> list[str]:
    """
    Names of mandatory referral groups missing from section 10.

    Each group needs one matching phrase. "structural" matches structural, PE/RA,
    or professional engineer. An empty section 10 falls back to the whole plan
    so a single referrals paragraph still counts.
    """
    ref_text = ""
    for section in payload.sections:
        if section.section_id in ("10", "section_10", "referrals"):
            ref_text += " ".join(c.text for c in section.claims).lower()
    if not ref_text:
        ref_text = " ".join(c.text for sec in payload.sections for c in sec.claims).lower()

    groups = [
        ("structural", ("structural", "pe/ra", "professional engineer")),
        ("roof", ("roof condition", "roof survey")),
        ("electric", ("licensed electrician", "electrician")),
        ("fire", ("fdny", "rooftop access")),
        ("utility", ("interconnection", "con edison", "utility interconnection")),
    ]
    return [name for name, keys in groups if not any(key in ref_text for key in keys)]


# "We cannot guarantee savings" declines a promise, it does not make one. Only a refusal that sits
# directly against the promise is removed ("cannot guarantee", "no guarantee", "not a guarantee").
# A "not" or "no" a few words earlier is left alone, so "it is not true we will save" still fails.
_NEGATED_PROMISE = re.compile(
    r"\b(?:cannot|can't|can not|do not|does not|don't|will not|won't|never|no|not|declin\w*(?: to)?)"
    r"\s+(?:(?:a|an|the|any|our|your|these|those)\s+)?(?:guarantee\w*|promise\w*|will save)",
    re.I,
)

# The user asked for a promise, or asked to use a rule from outside NYC.
_GUARANTEE_REQUEST = re.compile(r"\bguarantee", re.I)


def _has_promise_words(payload: RoadmapPayload) -> list[str]:
    """Promise words in the plan, ignoring sentences that refuse to promise ("cannot guarantee")."""
    hits = []
    for claim in _collect_claims(payload):
        lower = _NEGATED_PROMISE.sub(" ", claim.text.lower())
        for word in PROMISE_WORDS:
            if word in lower:
                hits.append(word)
    return hits


def _user_request_issues(user_message: str, combined_text: str) -> list[str]:
    """
    v6 (eval case 3): a request for a guarantee, or for a rule from outside NYC, must be declined
    in so many words. Saying nothing would let the user think the request was quietly accepted.
    """
    if not user_message:
        return []
    issues: list[str] = []
    if _GUARANTEE_REQUEST.search(user_message) and not _NEGATED_PROMISE.search(combined_text):
        issues.append("The user asked for a guarantee. Say plainly that savings cannot be guaranteed.")
    if _NON_NYC_RULE.search(user_message):
        excluded = any(
            _NON_NYC_RULE.search(sentence) and _RULE_EXCLUDED.search(sentence)
            for sentence in re.split(r"(?<=[.;])\s+", combined_text)
        )
        if not excluded:
            issues.append("The user asked to use a rule from outside NYC. Say it does not apply and leave it out.")
    return issues


# v6: plain words a reader would use for each tool, so section 12 can name a failure without tool ids.
_TOOL_PLAIN_NAMES: dict[str, tuple[str, ...]] = {
    "get_solar_production": ("pvwatts", "solar production", "solar sizing", "solar output", "solar"),
    "optimize_solar_storage": ("reopt", "battery"),
    "get_utility_rates": ("rate", "price"),
    "get_utility_tariff": ("tariff",),
    "lookup_ny_building_records": ("building record", "pluto", "public record"),
    "search_ny_incentives_and_rules": ("incentive",),
    "get_hazard_context": ("hazard", "fema", "flood"),
    "run_financial_model": ("financial model", "scenario"),
    "calculate": ("calculat",),
}
_FAILURE_WORDS = re.compile(
    r"\b(fail\w*|unavailable|error|did not return|could not|no data|not available|outage"
    r"|not sized|cannot be sized|not estimated|not costed|pending verification|no free roof)\b",
    re.I,
)

# v6 wording the run-context rules look for. Each is matched against lowercase claim text.
_VERIFY_ROOF = re.compile(
    r"verif\w*[^.]{0,100}(?:roof|usable|area)|(?:roof|usable|area)[^.]{0,100}verif\w*", re.I
)
_EXISTING_WORDS = re.compile(r"\b(existing|already|current(?:ly)?|in place|installed)\b", re.I)
_BUDGET_GAP_WORDS = re.compile(
    r"more than (?:your|the) budget|over budget|exceeds? (?:your |the )?budget|budget gap|funding gap"
    r"|above (?:your|the) budget|over (?:your|the) budget",
    re.I,
)
# "Scenario B", "Scenarios A and B", "Scenarios A, B and C": the capture holds the letters and joiners.
_SCENARIO_LIST = re.compile(r"\bscenarios?\s+([abc](?:\s*(?:,|and|&|or|/)\s*[abc]\b)*)\b", re.I)

# Numbers that need solar production data. When PVWatts failed and never succeeded, a claim citing one
# of these was built on an invented production figure.
_SOLAR_DEPENDENT_CALCS = {"C3", "C4", "F-B", "F-C"}
# A solar production figure, such as "60,000 kWh". A battery price of "$600/kWh" later in the
# same sentence does not count: the kWh has to follow the solar number, not a slash.
_SOLAR_KWH = re.compile(
    r"solar[^.]*?\d[\d,]*(?:\s*-\s*\d[\d,]*)?\s*kwh"
    r"|\d[\d,]*(?:\s*-\s*\d[\d,]*)?\s*kwh[^.]*solar",
    re.I,
)
# "Scenario B upfront cost is 120,000 USD" invents a solar scenario. A phase number, as in
# "Phase 5 ... (Scenario C)", does not. A sentence that says B or C are not costed yet is the honest gap.
_SCENARIO_BC_DEFERRED = re.compile(
    r"\b(not costed|not estimated|will be compared|once pvwatts|are missing|is missing)\b",
    re.I,
)
_SCENARIO_BC_FIGURE = re.compile(
    r"\bscenarios?\s+[bc]\b(?:(?!\bscenarios?\s+[bc]\b).){0,120}?"
    r"(?:\$\s*\d|\d[\d,]*(?:\.\d+)?(?:\s*-\s*\d[\d,]*(?:\.\d+)?)?\s*(?:%|usd|dollars?|kwh|kw\b|years?)"
    r"|\b(?:fifty|hundred|thousand)\b)",
    re.I,
)

# FEMA flood zones that mean a 1%-a-year (or coastal) flood risk.
_HIGH_RISK_FLOOD_ZONES = {"A", "AE", "AH", "AO", "AR", "A99", "V", "VE"}
# "elevate" / "elevated" / "elevation", but not "elevator". "raise" is a whole word, not "fundraise".
_FLOOD_PROTECTION = re.compile(
    r"\belevat(?:e|ed|ing|ion)\b|\babove the\b|\bflood-?proof\b|\braise\b",
    re.I,
)


def _section_text(payload: RoadmapPayload, section_id: str) -> str:
    """All claim text of one section, lowercased, or an empty string if the section is absent."""
    return " ".join(
        claim.text for section in payload.sections if section.section_id == section_id for claim in section.claims
    ).lower()


def _section_claims(payload: RoadmapPayload, section_id: str) -> list[str]:
    """Each claim in one section, lowercased. One claim is one statement, so words cannot leak across them."""
    return [
        claim.text.lower()
        for section in payload.sections
        if section.section_id == section_id
        for claim in section.claims
    ]


def _states_users_existing_solar(claim: Claim) -> bool:
    """
    True when the claim only repeats solar the user told us they already have.

    The user's own numbers (for example "the existing array makes 457,512 kWh a year", cited to the intake)
    are not invented production figures, so the no-solar-numbers rules leave them alone. Both things must
    hold: the claim cites the intake and it speaks of an existing or already-installed system.
    """
    return bool(claim.source_url and claim.source_url.startswith("session://") and _EXISTING_WORDS.search(claim.text))


def _invented_solar_figure(claim: Claim) -> bool:
    """True when this claim states a solar-production number or a cost that needs one."""
    if _states_users_existing_solar(claim):
        return False
    if (claim.calc_id or "") in _SOLAR_DEPENDENT_CALCS or _SOLAR_KWH.search(claim.text):
        return True
    if _SCENARIO_BC_DEFERRED.search(claim.text):
        return False
    return bool(_SCENARIO_BC_FIGURE.search(claim.text))


def _run_context_issues(payload: RoadmapPayload, notes: AgentNotes) -> list[str]:
    """
    v6 rules that depend on what happened in this run, not only on the roadmap text.

    - Every tool that failed (and never succeeded later) is named in the same section 12 claim as a failure.
    - When PVWatts failed, no claim states a solar kWh figure, an assumption of one, or a cost for scenario B or C.
    - No claim cites a page that was ignored for hidden instructions, and section 12 says it was ignored.
    - A high-risk flood zone needs flood protection in section 9 and an Appendix G review in section 10.
      A landmark needs an LPC review, and parkland needs a parkland-use review by counsel, both in section 10.
    """
    issues: list[str] = []
    gap_claims = _section_claims(payload, "12")
    gaps = " ".join(gap_claims)
    claims = _collect_claims(payload)

    for tool_name in notes.failed_tools:
        words = _TOOL_PLAIN_NAMES.get(tool_name, (tool_name.replace("_", " "),))
        # Hyphens count as spaces, so "building-records lookup failed" names the building records tool.
        reported = any(
            any(word in sentence.replace("-", " ") for word in words) and _FAILURE_WORDS.search(sentence)
            for sentence in gap_claims
        )
        if not reported:
            issues.append(f"Tool failure not reported in section 12: {tool_name}.")

    if "get_solar_production" in notes.failed_tools:
        for claim in claims:
            if _invented_solar_figure(claim):
                issues.append(f"Solar production number used after PVWatts failed: {claim.text[:80]}")

    issues.extend(_roof_and_existing_issues(payload, notes, claims))
    issues.extend(_intake_detail_issues(payload, notes, claims))
    issues.extend(_law_link_issues(payload))
    issues.extend(_budget_gap_issues(payload, notes))
    issues.extend(_calc_id_issues(claims, notes))

    quarantined = notes.quarantined_urls()
    if quarantined:
        for claim in claims:
            if claim.source_url and claim.source_url in quarantined:
                issues.append(f"Claim cites a page ignored for hidden instructions: {claim.text[:80]}")
        if not re.search(r"hidden|injected|ignored", gaps):
            issues.append("Section 12 must say a retrieved page was ignored for hidden instructions.")

    flood_zone = str(notes.site_context.get("flood_zone") or "").upper()
    resilience = _section_text(payload, "9")
    reviews = _section_text(payload, "10")
    if flood_zone in _HIGH_RISK_FLOOD_ZONES and not (
        "flood" in resilience and _FLOOD_PROTECTION.search(resilience)
    ):
        issues.append(
            f"Building is in flood zone {flood_zone}: section 9 must plan flood protection "
            "(for example elevating the battery and electrical equipment)."
        )
    if flood_zone in _HIGH_RISK_FLOOD_ZONES and "appendix g" not in reviews:
        issues.append(
            f"Building is in flood zone {flood_zone}: section 10 must include a flood-zone review "
            "under NYC Building Code Appendix G."
        )

    if notes.site_context.get("landmark") and not ("landmarks preservation" in reviews or "lpc" in reviews):
        issues.append("Landmark building: section 10 must include a Landmarks Preservation Commission (LPC) review.")
    if notes.site_context.get("parkland") and not ("parkland" in reviews and "counsel" in reviews):
        issues.append("Building is on parkland: section 10 must include a parkland use review by counsel.")
    # On city parkland the Landmarks Commission advises the owning agency instead of issuing a permit.
    if (
        notes.site_context.get("parkland")
        and notes.site_context.get("landmark")
        and ("landmarks preservation" in reviews or "lpc" in reviews)
        and "advisory" not in reviews
    ):
        issues.append(
            "The building is a landmark on city parkland: the LPC gives an advisory report to the owning agency, "
            "not a permit. Say so in section 10."
        )
    return issues


def _roof_and_existing_issues(payload: RoadmapPayload, notes: AgentNotes, claims: list[Claim]) -> list[str]:
    """
    v6 rules for the roof and for systems the building already has.

    - A roof that is not flat: the plan tells the user to have an engineer or roofer verify the usable roof
      area (section 5 or 10). Until a verified area is in the intake, no claim may state a solar kWh figure or
      cost scenario B or C, because the flat-roof sizing does not apply.
    - Existing renewable or efficiency systems the user listed: section 2 or 4 must say they were taken
      into account, so the plan is not written as if the building started from nothing.
    """
    issues: list[str] = []
    roof_kind_now = notes.site_context.get("roof_kind")
    if roof_kind_now == "non_flat":
        where = [text for sid in ("5", "10") for text in _section_claims(payload, sid)]
        if not any(_VERIFY_ROOF.search(text) for text in where):
            issues.append(
                "The roof is not flat: section 5 or 10 must tell the user to have an engineer or roofer verify "
                "the usable roof area before any solar is designed."
            )
        if not notes.site_context.get("verified_usable_roof_sqft"):
            for claim in claims:
                if _invented_solar_figure(claim) and "get_solar_production" not in notes.failed_tools:
                    issues.append(f"Solar number used for a roof that is not flat and not verified: {claim.text[:80]}")
    if notes.site_context.get("existing_systems"):
        where = " ".join(_section_claims(payload, "2") + _section_claims(payload, "4"))
        if not _EXISTING_WORDS.search(where):
            issues.append(
                "The intake lists existing systems (" + str(notes.site_context["existing_systems"])[:80]
                + "): section 2 or 4 must say how they were taken into account."
            )
    return issues


_SCHOOL_OWNER_WORDS = re.compile(r"\bDCAS\b|public schools|\bSCA\b|school construction authority", re.I)
_REROOF_WORDS = re.compile(
    r"re-?roof\w*|roof[^.]{0,40}(?:replac|repair)\w*|(?:replac|repair)\w*[^.]{0,20}roof", re.I
)
_FUEL_WORDS = re.compile(r"natural gas|\boil\b|\bsteam\b|non-electric|heating fuel|\bfuel\b|gas[- ]fired", re.I)
_NOT_MODELED_WORDS = re.compile(r"not modeled|does not model|did not model|not calculated|not covered|outside (?:the|this) model", re.I)
_ANNUAL_BUDGET_WORDS = re.compile(r"annual|per year|each year|every year|yearly", re.I)
_UPFRONT_WORDS = re.compile(r"total|upfront|up-front|one-time|lump", re.I)
_LED_WORD = re.compile(r"\bLED\b")
_LED_ALREADY = re.compile(
    r"\b(?:already|existing|installed|have|has|in place|beyond|no further|nothing more|not a new)\b", re.I
)


_LAW_MENTION = re.compile(
    r"\bLocal Law \d+|\bLL ?\d{2,3}\b|elective pay|direct pay|\bNY-Sun\b|\bU\.S\.C\.|\bIRC \d+", re.I
)


def _law_link_issues(payload: RoadmapPayload) -> list[str]:
    """
    v7: in section 7 (cost, financing and incentives), a FACT or ESTIMATE that names a law or incentive program must
    carry a web link to its source.

    A calculation id or the intake is not a source for a law, and without a link the reader cannot check the
    rule. Only section 7 is held to this so far: it is where rules turn into dollars.
    """
    issues = []
    for section in payload.sections:
        if section.section_id != "7":
            continue
        for claim in section.claims:
            if claim.label not in ("FACT", "ESTIMATE") or not _LAW_MENTION.search(claim.text):
                continue
            if not str(claim.source_url or "").startswith(("http://", "https://")):
                issues.append(f"A law or program is named without a web link to its source: {claim.text[:80]}")
    return issues


_SNAKE_CASE = re.compile(r"\b[a-z]{2,}(?:_[a-z0-9]+)+\b")
_INTERNAL_ID = re.compile(r"\b(?:A[1-9]\d?|C[1-4]|F-[ABC])\b")
_TEAM_WORDS = re.compile(r"\bteam (?:placeholder|estimate|figure)s?\b|\bplaceholder\b", re.I)


def _plain_language_issues(payload: RoadmapPayload) -> list[str]:
    """
    v7: a plan written for a facilities manager must not use the code's own words.

    Rejected in any claim: internal field and flag names (words_with_underscores) and "team placeholder" / "placeholder".
    Rejected in claims that are not assumptions: internal ids (A7, C1, F-B); the id belongs in the claim's assumption_id or
    calc_id field, not in its sentence. An assumption sentence may begin with its id ("A4: ..."), which the screen strips.
    Enforced for live runs only, so saved recordings made before this rule still replay as they were.
    """
    issues: list[str] = []
    for section in payload.sections:
        for claim in section.claims:
            text = claim.text
            if _SNAKE_CASE.search(text):
                issues.append(f"Internal field or flag name in the text (write it in plain words): {text[:80]}")
            if _TEAM_WORDS.search(text):
                issues.append(f"Say 'planning estimate', not 'team placeholder' or 'placeholder': {text[:80]}")
            if claim.label != "ASSUMPTION" and _INTERNAL_ID.search(text):
                issues.append(f"Internal id (like A7, C1 or F-B) in the text; put it in the id field instead: {text[:80]}")
    return issues


PLAIN_ANSWER_MIN_WORDS = 50
PLAIN_ANSWER_MAX_WORDS = 240
_NUMBER_TOKEN = re.compile(r"\$?\d[\d,]*(?:\.\d+)?\s*(?:thousand|million|k|m)?\b", re.I)
# Phrases that mean the paragraph is talking about entered values or records that disagree. That belongs in the "Confirm first"
# list, not in the opening answer, so the paragraph is kept to the answer, the plan and the goal.
_RECORD_MISMATCH_TALK = ("line up", "differs from the city", "differ from the city", "city lists the lot", "tax-lot record", "does not match the city", "do not match the city")


def _number_values(text: str) -> list[float]:
    """The numbers in a sentence as plain values ("$40k" is 40000, "226,605" is 226605), years left out."""
    values: list[float] = []
    for token in _NUMBER_TOKEN.findall(text):
        raw = token.strip().lower().lstrip("$")
        scale = 1.0
        for word, factor in (("thousand", 1e3), ("million", 1e6), ("k", 1e3), ("m", 1e6)):
            if raw.endswith(word):
                raw, scale = raw[: -len(word)].strip(), factor
                break
        try:
            value = float(raw.replace(",", "")) * scale
        except ValueError:
            continue
        if value.is_integer() and 1900 <= value <= 2100:
            continue  # a year
        values.append(value)
    return values


def _plain_answer_issues(payload: RoadmapPayload, notes: AgentNotes | None, *, required: bool) -> list[str]:
    """
    v8: the plan opens with one plain-words answer to the question, and it must be safe to put first.

    Required in live runs (a missing answer sends the plan back once). Whenever one is present it must be the right length,
    use no promise wording, no internal names or ids, and state no number that is not already in the plan's own statements, so
    it cannot say more than the plan supports. It must explain it when solar was ruled out by the roof rules. It must NOT
    talk about entered values that differ from the city's records: those go in the "Confirm first" list instead.
    """
    text = (payload.plain_answer or "").strip()
    if not text:
        return ["The plan has no plain-words answer at the top. Write one short paragraph in `plain_answer` that answers the question."] if required else []
    issues: list[str] = []
    words = len(text.split())
    if words < PLAIN_ANSWER_MIN_WORDS or words > PLAIN_ANSWER_MAX_WORDS:
        issues.append(f"The plain-words answer is {words} words; it should be about {PLAIN_ANSWER_MIN_WORDS} to {PLAIN_ANSWER_MAX_WORDS}.")
    lowered = _NEGATED_PROMISE.sub(" ", text.lower())
    promises = [word for word in PROMISE_WORDS if word in lowered]
    if promises:
        issues.append(f"Promise wording in the plain-words answer: {', '.join(sorted(set(promises)))}")
    if _SNAKE_CASE.search(text) or _INTERNAL_ID.search(text):
        issues.append("The plain-words answer uses an internal name or id (write it in plain words).")

    # No number the plan's own statements do not contain.
    known: list[float] = []
    for claim in _collect_claims(payload):
        known.extend(_number_values(claim.text))
        known.extend(float(v) for v in (claim.value_low, claim.value_high) if v is not None)
    def supported(value: float) -> bool:
        if value < 10:
            return True  # counts and small rounded numbers ("two scenarios", "6 to 18")
        return any(abs(value - k) <= max(0.03 * abs(k), 0.6) for k in known)
    unsupported = [v for v in _number_values(text) if not supported(v)]
    if unsupported:
        shown = ", ".join(f"{v:,.0f}" if v >= 100 else f"{v:g}" for v in unsupported[:4])
        issues.append(f"The plain-words answer states numbers that are not in the plan's statements: {shown}. Use only numbers the sections give.")

    lower = text.lower()
    if any(phrase in lower for phrase in _RECORD_MISMATCH_TALK):
        issues.append("Leave record mismatches (an address, floor area or output that differs from the city's records) out of the plain-words answer. They are listed under \"Confirm first\" already.")

    if notes is not None:
        from tools.roof import plain_refusal

        if any(plain_refusal(str(err)) for err in notes.failed_tools.values()):
            if "solar" not in lower or not any(word in lower for word in ("roof", "room", "space", "engineer", "roofer")):
                issues.append("The plain-words answer must say why solar was not sized (the roof rules turned it down) and what that means.")
    return issues


def _intake_detail_issues(payload: RoadmapPayload, notes: AgentNotes, claims: list[Claim]) -> list[str]:
    """
    v7 rules for the optional intake answers (owner, roof condition, lighting, heating fuel, goal type, budget type).

    Each rule only fires when the user answered that question, so a skipped question adds no requirement:
    - all-LED lighting: LED cannot be recommended as a new measure.
    - a poor roof: re-roofing is mentioned (sections 5, 8 or 10) because solar should not go on a failing roof.
    - school owner (DOE): the plan names DCAS, NYC Public Schools or the SCA as the route (section 10).
    - heating fuel that is not electricity: the plan says the fuel is outside an electricity goal (sections 2, 4 or 6).
    - a goal that is not a percent cut: the plan says that goal is not modeled (section 1 or 12).
    - an annual budget: the plan says the model treats the amount as one total (sections 6, 7 or 12).
    """
    issues: list[str] = []
    site = notes.site_context
    if site.get("lighting_type") == "led_all":
        for claim in claims:
            if (
                claim.label == "RECOMMENDATION"
                and _LED_WORD.search(claim.text)
                and not _LED_ALREADY.search(claim.text)
            ):
                issues.append(f"LED lighting recommended as a new measure, but the user says all lighting is LED: {claim.text[:80]}")
    if site.get("roof_condition") == "poor" or site.get("roof_age_20_plus"):
        where = [t for sid in ("5", "8", "10") for t in _section_claims(payload, sid)]
        if not any(_REROOF_WORDS.search(t) for t in where):
            issues.append(
                "The roof is rated poor or is 20 years old or more (the user or the city's LL24 record says so): "
                "section 5, 8 or 10 must say the roof may need replacing or repair before solar."
            )
    if site.get("owner_agency") == "doe":
        if not any(_SCHOOL_OWNER_WORDS.search(t) for t in _section_claims(payload, "10")):
            issues.append("The building is a DOE school: section 10 must name DCAS, NYC Public Schools or the SCA as the approval route.")
    fuel = site.get("heating_fuel")
    if fuel and fuel != "electric":
        where = [t for sid in ("2", "4", "6") for t in _section_claims(payload, sid)]
        if not any(_FUEL_WORDS.search(t) for t in where):
            issues.append("Heating is not electric: section 2, 4 or 6 must say the heating fuel is outside an electricity-use goal.")
    goal_type = site.get("goal_type")
    if goal_type and goal_type != "percent_reduction":
        where = [t for sid in ("1", "12") for t in _section_claims(payload, sid)]
        if not any(_NOT_MODELED_WORDS.search(t) for t in where):
            issues.append("The goal is not a percent cut in electricity: section 1 or 12 must say that goal is not modeled.")
    if site.get("budget_type_annual"):
        where = [t for sid in ("6", "7", "12") for t in _section_claims(payload, sid)]
        if not any(_ANNUAL_BUDGET_WORDS.search(t) and _UPFRONT_WORDS.search(t) for t in where):
            issues.append("The budget is annual: section 6, 7 or 12 must say the model treats the amount as one total upfront figure.")
    return issues


def _budget_gap_issues(payload: RoadmapPayload, notes: AgentNotes) -> list[str]:
    """
    v6: when any scenario costs more than the budget, section 6 or 7 must say so in plain words.

    Reaching the goal can take more than the money set aside. The plan states the gap instead of hiding the
    scenario, and leaves the choice to extend the budget with the user.
    """
    over = [
        cid
        for cid, data in notes.calculations.items()
        if cid.startswith("F-") and (data.get("budget_gap_usd") or [0, 0])[1] > 0
    ]
    if not over:
        return []
    text = " ".join(_section_claims(payload, "6") + _section_claims(payload, "7"))
    if _BUDGET_GAP_WORDS.search(text):
        return []
    return [
        "Scenario(s) " + ", ".join(sorted(over)) + " cost more than the budget: section 6 or 7 must state how much "
        "more than the budget they cost (the tool's budget_note), so the user can weigh extending it."
    ]


def _calc_id_issues(claims: list[Claim], notes: AgentNotes) -> list[str]:
    """
    v6: a cited calculation must be one this run actually produced, and a scenario claim must cite its own.

    A claim about "Scenario B" that cites F-A would send a reader to the wrong numbers. A calc_id that no
    tool returned in this run (a made-up C5, or F-D) cannot be traced at all.
    """
    issues: list[str] = []
    have = set(notes.calculations)
    for claim in claims:
        cid = (claim.calc_id or "").strip()
        if not cid:
            continue
        if cid not in have:
            issues.append(f"Claim cites calculation {cid}, which was not run in this analysis: {claim.text[:60]}")
            continue
        letters = _scenario_letters(claim.text)
        if cid.startswith("F-") and letters and cid[-1] not in letters:
            issues.append(f"Claim is about scenario {'/'.join(sorted(letters))} but cites {cid}: {claim.text[:60]}")
    return issues


def _scenario_letters(text: str) -> set[str]:
    """
    Every scenario letter a claim names, so "Scenarios A and B" gives {A, B} and "Scenario C" gives {C}.

    The cited F-x only has to be one of them: a sentence about A and B may cite either.
    """
    letters: set[str] = set()
    for match in _SCENARIO_LIST.finditer(text):
        letters.update(letter.upper() for letter in re.findall(r"[abc]", match.group(1), re.I))
    return letters


def run_check4(
    payload: RoadmapPayload,
    *,
    assumptions_register: dict[str, str] | None = None,
    user_message: str = "",
    require_all_sections: bool = True,
    notes: AgentNotes | None = None,
    plain_language: bool = False,
    require_plain_answer: bool = False,
) -> CheckResult:
    """
    Share gate: labels, sections, NYC-only rules, referrals, and no closed program in net cost.

    Pass assumptions_register from AgentNotes so ASSUMPTION claims can point at A1, A2, …
    Pass user_message so "skip the engineer" can be declined without stopping the rest of the plan.
    require_all_sections is False for a short follow-up answer, which is not a 13-section plan.
    Pass notes (v6) to also apply the run-context rules in _run_context_issues; they only run
    for a full roadmap, because a short follow-up answer has no section 9, 10 or 12.
    One fix loop is handled in the harness; this function only evaluates once.
    """
    register = assumptions_register or {}
    issues: list[str] = []
    for section in payload.sections:
        for claim in section.claims:
            has_number = _claim_has_number(claim.text, claim.value_low)
            missing_number_fields = has_number and (
                claim.label not in _LABELS
                or not claim.confidence
                or not _claim_has_id(claim.source_url, claim.calc_id, claim.assumption_id)
            )
            if missing_number_fields:
                issues.append(f"Unlabeled number: {claim.text[:80]}")
            else:
                if claim.label not in _LABELS:
                    issues.append(f"Unlabeled or invalid label on claim: {claim.text[:60]}")
                ok, trace_issue = _claim_traceability_ok(claim, register)
                if not ok:
                    issues.append(f"Claim {trace_issue}: {claim.text[:60]}")
                if not claim.confidence:
                    issues.append(f"Claim missing confidence: {claim.text[:60]}")
            issues.extend(_non_nyc_rule_issues(section.section_id, claim.text))
            closed = _closed_in_net_cost_issue(section.section_id, claim.text)
            if closed:
                issues.append(closed)

    if require_all_sections:
        issues.extend(_missing_section_issues({section.section_id for section in payload.sections}))

    missing_referrals = _missing_referral_groups(payload)
    if missing_referrals:
        issues.append(
            "Mandatory professional referrals are incomplete in section 10 ("
            + ", ".join(missing_referrals)
            + ")."
        )

    combined = " ".join(claim.text for claim in _collect_claims(payload))
    issues.extend(_skip_engineer_issues(user_message, combined))
    issues.extend(_user_request_issues(user_message, combined))

    if notes is not None and require_all_sections:
        issues.extend(_run_context_issues(payload, notes))
    if plain_language:
        issues.extend(_plain_language_issues(payload))
    if require_all_sections:
        issues.extend(_plain_answer_issues(payload, notes, required=require_plain_answer))

    promises = _has_promise_words(payload)
    if promises:
        issues.append(f"Promise wording detected: {', '.join(sorted(set(promises)))}")

    if issues:
        return CheckResult.fail("check4_fail", "; ".join(issues), issues=issues)

    return CheckResult.ok("check4_pass", "Roadmap claims, referrals, and wording checks passed.")
