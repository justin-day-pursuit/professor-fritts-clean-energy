"""
Structured claims and roadmap payload the LLM must produce via write_roadmap / write_answer.

Check 4 walks these objects; the Markdown renderer turns them into downloadable sections.
v2 adds value ranges and units to each claim and names all 13 PRD sections in one place.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Label = Literal["FACT", "ESTIMATE", "ASSUMPTION", "RECOMMENDATION"]
Confidence = Literal["high", "medium", "low"]

# Wording Check 4 looks for in section 10 referrals (substring match, case-insensitive).
MANDATORY_REFERRAL_KEYWORDS: list[str] = [
    "structural",
    "pe/ra",
    "professional engineer",
    "roof condition",
    "roof survey",
    "licensed electrician",
    "fdny",
    "rooftop access",
    "interconnection",
    "con edison",
    "utility interconnection",
]

# The 13 sections of the plan, in the order the PRD requires. The renderer prints them in this
# order, and the "missing section" check in v3 will use the same list. Change a title here and
# it changes everywhere.
SECTION_TITLES: dict[str, str] = {
    "1": "Summary and goal status",
    "2": "Building profile and data provenance",
    "3": "Assumptions register",
    "4": "Baseline and efficiency opportunities",
    "5": "Solar assessment with calculations",
    "6": "Scenario comparison table",
    "7": "Cost, financing and incentives",
    "8": "Priority roadmap",
    "9": "Resilience and reliability plan",
    "10": "Required professional reviews and permits",
    "11": "Path to net-zero and learning resources",
    "12": "Gaps, conflicts and confidence summary",
    "13": "Sources",
}

PROMISE_WORDS = ("guarantee", "will save", "guaranteed savings")


class Claim(BaseModel):
    """
    One labeled statement with traceability rules enforced in Check 4.

    FACT, ESTIMATE, and RECOMMENDATION need source_url or calc_id.
    ASSUMPTION needs assumption_id (A1, A2, …) that exists in the run notes register.
    """

    text: str
    label: Label
    confidence: Confidence
    source_url: str | None = None
    calc_id: str | None = None
    assumption_id: str | None = None
    # v2: a number is a range, not a single value. When the claim is about one figure, put the
    # low and high ends here with the unit ("kWh/yr", "USD", "%"). A single figure repeats it
    # in both. Claims that are only words leave all three empty.
    value_low: float | None = None
    value_high: float | None = None
    units: str | None = None

    @model_validator(mode="after")
    def range_is_ordered(self) -> "Claim":
        """
        Keep ranges sensible: both ends or neither, low not above high, and a unit when numbers exist.

        If you add a new numeric field to Claim, check it here too.
        """
        has_low = self.value_low is not None
        has_high = self.value_high is not None
        if has_low != has_high:
            raise ValueError("value_low and value_high must be given together")
        if has_low and self.value_low > self.value_high:  # type: ignore[operator]
            raise ValueError("value_low must not be above value_high")
        if has_low and not self.units:
            raise ValueError("a value range needs units (for example 'kWh/yr' or 'USD')")
        return self

    @field_validator("source_url", "calc_id", "assumption_id", "units", mode="before")
    @classmethod
    def empty_to_none(cls, v: Any) -> Any:
        """
        Treat blank strings from the LLM as missing optional fields.

        Check 4 and the database expect None when a claim omits source, calc, or assumption id;
        if you add another optional string field on Claim, include its name in this validator list.
        """
        if v == "":
            return None
        return v


class RoadmapSection(BaseModel):
    """A numbered PRD section filled with claims."""

    section_id: str
    title: str
    claims: list[Claim] = Field(default_factory=list)
    stand_in_note: str | None = None


class RoadmapPayload(BaseModel):
    """
    Final structured answer before rendering — all 13 PRD sections from v2 on.

    The renderer prints a "not provided" line for any section the model left out, so the reader
    always sees 13 sections in order. footer_note is optional extra text for the end of the plan.
    """

    sections: list[RoadmapSection] = Field(default_factory=list)
    footer_note: str = ""


class WriteRoadmapInput(BaseModel):
    """Schema for the write_roadmap final tool."""

    roadmap: RoadmapPayload


class WriteAnswerInput(BaseModel):
    """Follow-up chat answer with the same claim rules as a mini-roadmap."""

    summary: str
    claims: list[Claim] = Field(default_factory=list)
