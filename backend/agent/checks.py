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
    "get_solar_production": ("pvwatts", "solar production"),
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
    r"\b(fail\w*|unavailable|error|did not return|could not|no data|not available|outage)\b", re.I
)

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


def _invented_solar_figure(claim: Claim) -> bool:
    """True when this claim states a solar-production number or a cost that needs one."""
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
    return issues


def run_check4(
    payload: RoadmapPayload,
    *,
    assumptions_register: dict[str, str] | None = None,
    user_message: str = "",
    require_all_sections: bool = True,
    notes: AgentNotes | None = None,
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

    promises = _has_promise_words(payload)
    if promises:
        issues.append(f"Promise wording detected: {', '.join(sorted(set(promises)))}")

    if issues:
        return CheckResult.fail("check4_fail", "; ".join(issues), issues=issues)

    return CheckResult.ok("check4_pass", "Roadmap claims, referrals, and wording checks passed.")
