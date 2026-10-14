"""
Structured claims and roadmap payload the LLM must produce via write_roadmap / write_answer.

Check 4 walks these objects; the Markdown renderer turns them into downloadable sections.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

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

    @field_validator("source_url", "calc_id", "assumption_id", mode="before")
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
    Final structured answer before rendering — sections 1,2,3,5,6,8,9,10,12,13 in v0.

    Footer text names sections 4, 7, 11 as later blocks.
    """

    sections: list[RoadmapSection] = Field(default_factory=list)
    footer_note: str = (
        "Sections 4 (baseline efficiency detail), 7 (cost and financing), and 11 (net-zero path) "
        "are owned by v2/v5 and are not included in this v0 stand-in."
    )


class WriteRoadmapInput(BaseModel):
    """Schema for the write_roadmap final tool."""

    roadmap: RoadmapPayload


class WriteAnswerInput(BaseModel):
    """Follow-up chat answer with the same claim rules as a mini-roadmap."""

    summary: str
    claims: list[Claim] = Field(default_factory=list)
