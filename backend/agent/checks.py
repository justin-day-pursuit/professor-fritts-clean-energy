"""
Code-enforced safety checks 1–4 from the agent-flow diagram.

Each returns a dict logged as a RunEvent; passed=False stops or flags the run as documented.
"""

from __future__ import annotations

import re
from typing import Any

from agent.claims import (
    MANDATORY_REFERRAL_KEYWORDS,
    PROMISE_WORDS,
    Claim,
    RoadmapPayload,
)
from agent.limits import RunLimits, tool_call_limit, tool_retry_limit
from tools.base import ToolResult
from tools.cache import is_stale
from tools.registry import get_tool_spec, list_tool_names, validate_tool_input

# Simple injection-style phrases Check 3 flags (full defense tests arrive in v6).
HIDDEN_INSTRUCTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"<\s*script", re.I),
]

NY_STATE_CODES = {"NY", "NEW YORK", "NYC", "NEW YORK CITY"}


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
    Start gate: New York only; budget and goal required or ask once (needs_input).

    Out-of-state buildings stop with out_of_scope; missing fields get one clarifying question.
    """
    state = _profile_state(profile)
    if state and state not in NY_STATE_CODES and "NEW YORK" not in state:
        # Treat obvious non-NY (e.g. NJ) as out of scope.
        if state in ("NJ", "NEW JERSEY", "PA", "CONNECTICUT", "CT"):
            return CheckResult.fail(
                "out_of_scope",
                "Professor Fritts v0 supports New York public buildings only.",
                stop_reason="out_of_scope",
            )

    missing: list[str] = []
    if not state or (state not in NY_STATE_CODES and "NEW YORK" not in state):
        missing.append("state (New York)")
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

    return CheckResult.ok("check1_pass", "New York building with budget and goal present.")


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

    retries = limits.retries_by_tool.get(tool_name, 0)
    if retries >= tool_retry_limit():
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

    stale = result.stale or is_stale(result.retrieved_at, freshness_kind)
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


def _claim_has_source(claim: Claim) -> bool:
    if claim.label in ("FACT", "ESTIMATE"):
        return bool(claim.source_url or claim.calc_id)
    return bool(claim.source_url or claim.calc_id or claim.label == "ASSUMPTION")


def _collect_claims(payload: RoadmapPayload) -> list[Claim]:
    claims: list[Claim] = []
    for section in payload.sections:
        claims.extend(section.claims)
    return claims


def _referrals_present(payload: RoadmapPayload) -> bool:
    """True when section 10 text hits every mandatory referral keyword bucket."""
    ref_text = ""
    for section in payload.sections:
        if section.section_id in ("10", "section_10", "referrals"):
            ref_text += " ".join(c.text for c in section.claims).lower()
    if not ref_text:
        ref_text = " ".join(c.text for sec in payload.sections for c in sec.claims).lower()

    for keyword in MANDATORY_REFERRAL_KEYWORDS:
        if keyword.lower() not in ref_text:
            # Allow grouped keywords: structural OR pe/ra handled by list
            pass

    # Require at least one match from each thematic group
    groups = [
        ("structural", ("structural", "pe/ra", "professional engineer")),
        ("roof", ("roof condition", "roof survey")),
        ("electric", ("licensed electrician", "electrician")),
        ("fire", ("fdny", "rooftop access")),
        ("utility", ("interconnection", "con edison", "utility interconnection")),
    ]
    for _name, keys in groups:
        if not any(k in ref_text for k in keys):
            return False
    return True


def _has_promise_words(payload: RoadmapPayload) -> list[str]:
    hits = []
    for claim in _collect_claims(payload):
        lower = claim.text.lower()
        for word in PROMISE_WORDS:
            if word in lower:
                hits.append(word)
    return hits


def run_check4(payload: RoadmapPayload) -> CheckResult:
    """
    Share gate: labels, sources, mandatory referrals, no promise words.

    One fix loop is handled in the harness; this function only evaluates once.
    """
    issues: list[str] = []
    for claim in _collect_claims(payload):
        if claim.label not in ("FACT", "ESTIMATE", "ASSUMPTION", "RECOMMENDATION"):
            issues.append(f"Unlabeled or invalid label on claim: {claim.text[:60]}")
        if not _claim_has_source(claim):
            issues.append(f"Claim missing source_url or calc_id: {claim.text[:60]}")
        if not claim.confidence:
            issues.append(f"Claim missing confidence: {claim.text[:60]}")

    if not _referrals_present(payload):
        issues.append("Mandatory professional referrals are incomplete in section 10.")

    promises = _has_promise_words(payload)
    if promises:
        issues.append(f"Promise wording detected: {', '.join(sorted(set(promises)))}")

    if issues:
        return CheckResult.fail("check4_fail", "; ".join(issues), issues=issues)

    return CheckResult.ok("check4_pass", "Roadmap claims, referrals, and wording checks passed.")
