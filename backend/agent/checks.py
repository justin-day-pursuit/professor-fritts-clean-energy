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
from tools.base import ToolResult
from tools.cache import is_stale_for_tool
from tools.registry import get_tool_spec, list_tool_names, validate_tool_input

# Simple injection-style phrases Check 3 flags (full defense tests arrive in v6).
HIDDEN_INSTRUCTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"<\s*script", re.I),
]

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
    goal = profile.get("goal") or profile.get("energy_goal")
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
) -> CheckResult:
    """
    Tool gate: registered tool, valid schema, under call/retry/time limits.

    Final tools write_roadmap / write_answer skip registry lookup when is_final_tool=True.
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

    return CheckResult.ok("check2_pass", f"Tool {tool_name} approved.")


def run_check3(result: ToolResult, *, freshness_kind: str = "default") -> CheckResult:
    """
    Answer gate: provenance fields, stale flag, injection pattern scan on serialized data.

    Results are treated as data only; any hidden-instruction match adds a flag.
    """
    missing = []
    if not result.source_url:
        missing.append("source_url")
    if not result.retrieved_at and result.tool != "get_building_profile" and result.tool != "calculate":
        missing.append("retrieved_at")
    if not result.dataset_version and result.tool != "get_building_profile":
        missing.append("dataset_version")

    flags: list[str] = list(result.flags)
    blob = str(result.data)
    for pattern in HIDDEN_INSTRUCTION_PATTERNS:
        if pattern.search(blob):
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
    if _CERTIFIES_ROOF.search(combined_text):
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


def _has_promise_words(payload: RoadmapPayload) -> list[str]:
    hits = []
    for claim in _collect_claims(payload):
        lower = claim.text.lower()
        for word in PROMISE_WORDS:
            if word in lower:
                hits.append(word)
    return hits


def run_check4(
    payload: RoadmapPayload,
    *,
    assumptions_register: dict[str, str] | None = None,
    user_message: str = "",
    require_all_sections: bool = True,
) -> CheckResult:
    """
    Share gate: labels, sections, NYC-only rules, referrals, and no closed program in net cost.

    Pass assumptions_register from AgentNotes so ASSUMPTION claims can point at A1, A2, …
    Pass user_message so "skip the engineer" can be declined without stopping the rest of the plan.
    require_all_sections is False for a short follow-up answer, which is not a 13-section plan.
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

    promises = _has_promise_words(payload)
    if promises:
        issues.append(f"Promise wording detected: {', '.join(sorted(set(promises)))}")

    if issues:
        return CheckResult.fail("check4_fail", "; ".join(issues), issues=issues)

    return CheckResult.ok("check4_pass", "Roadmap claims, referrals, and wording checks passed.")
