"""
Label coverage: does every number in a plan carry a label, a confidence and an ID?

This is the v2 goalpost script. It is separate from Check 4 on purpose: Check 4 blocks a bad plan,
this module only measures and reports, so a person (or a test) can see "100% covered" or exactly
which claims are missing something.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from agent.claims import Claim, RoadmapPayload

LABELS = {"FACT", "ESTIMATE", "ASSUMPTION", "RECOMMENDATION"}
CONFIDENCES = {"high", "medium", "low"}

# Any digit counts as "a number" — dates, dollars, percents and counts all need a label too.
_HAS_DIGIT = re.compile(r"\d")


def claim_has_number(claim: Claim) -> bool:
    """True when the claim states a number, either in its range fields or in its text."""
    return claim.value_low is not None or bool(_HAS_DIGIT.search(claim.text))


def claim_problems(claim: Claim) -> list[str]:
    """List what a numeric claim is missing: label, confidence, or an ID (source, calc or assumption)."""
    problems = []
    if claim.label not in LABELS:
        problems.append("label")
    if claim.confidence not in CONFIDENCES:
        problems.append("confidence")
    if not (claim.source_url or claim.calc_id or claim.assumption_id):
        problems.append("id")
    return problems


@dataclass
class CoverageReport:
    """Result of one coverage run: how many numeric claims there were and which ones fell short."""

    numeric_claims: int = 0
    covered: int = 0
    failures: list[dict] = field(default_factory=list)

    @property
    def percent(self) -> float:
        """Share of numeric claims that are fully covered; an empty plan counts as 0, not 100."""
        if self.numeric_claims == 0:
            return 0.0
        return 100.0 * self.covered / self.numeric_claims

    @property
    def complete(self) -> bool:
        """True only when there is at least one number and every number is covered."""
        return self.numeric_claims > 0 and self.covered == self.numeric_claims


def check_coverage(payload: RoadmapPayload) -> CoverageReport:
    """Walk every claim in the plan and score the ones that contain a number."""
    report = CoverageReport()
    for section in payload.sections:
        for claim in section.claims:
            if not claim_has_number(claim):
                continue
            report.numeric_claims += 1
            problems = claim_problems(claim)
            if problems:
                report.failures.append(
                    {"section": section.section_id, "text": claim.text[:80], "missing": problems}
                )
            else:
                report.covered += 1
    return report
