"""
Fritts's working notes — facts, calculations, assumptions, sources, and tool log.

The harness serializes a short summary into the next LLM think step.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from tools.base import ToolResult


class AgentNotes(BaseModel):
    """
    In-memory state for one run; saved inside run output for debugging.

    To extend: add fields here and mention them in summarize_for_llm().
    """

    building_facts: dict[str, Any] = Field(default_factory=dict)
    calculations: dict[str, Any] = Field(default_factory=dict)
    # Every calculate call, not only the last one per formula. C4 is run three times for a savings range.
    calculation_runs: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    assumptions: dict[str, str] = Field(default_factory=dict)
    sources: list[dict[str, str]] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)

    def record_tool_result(self, tool_name: str, result: ToolResult) -> None:
        """Append provenance and payload snippets after Check 3 passes."""
        entry = {
            "tool": tool_name,
            "mock": result.mock,
            "source_url": result.source_url,
            "retrieved_at": result.retrieved_at,
            "data_keys": list(result.data.keys()),
        }
        self.tool_calls.append(entry)
        if result.source_url:
            self.sources.append(
                {
                    "tool": tool_name,
                    "source_url": result.source_url,
                    "retrieved_at": result.retrieved_at,
                }
            )
        if tool_name == "get_building_profile":
            self.building_facts.update(result.data.get("profile", {}))
            # A7 (v2): until a building model exists (phase 2), efficiency savings are a benchmark range.
            self.assumptions.setdefault(
                "A7",
                "Efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.",
            )

        # Check 4 only accepts an ASSUMPTION whose id is already in this register.
        # Tools fill the ids below so the model does not have to invent them.
        # A1 loss band, A2 setback, A3 sq ft per kW, A4 mock battery, A5 mock incentives, A6 mock hazards, A7 efficiency benchmark (set when the profile is read).
        if tool_name == "get_solar_production" and "range_assumption" in result.data:
            self.assumptions.setdefault("A1", str(result.data["range_assumption"]))

        if tool_name == "calculate" and "calc_id" in result.data:
            cid = result.data["calc_id"]
            self.calculations[cid] = result.data
            self.calculation_runs.setdefault(cid, []).append(
                {
                    "value": result.data.get("value"),
                    "units": result.data.get("units"),
                    "inputs": result.data.get("inputs") or {},
                }
            )
            if cid == "C1":
                factor = result.data.get("inputs", {}).get("setback_factor", 0.55)
                self.assumptions.setdefault("A2", f"Usable roof setback factor {factor} (C1)")
            elif cid == "C2":
                density = result.data.get("inputs", {}).get("sqft_per_kw", 66)
                self.assumptions.setdefault("A3", f"Array density factor {density} sq ft/kW DC (C2)")
            # A caller can still attach an id. setdefault keeps a tool-written sentence if one exists.
            for aid in result.data.get("assumption_ids") or []:
                key = str(aid)
                self.assumptions.setdefault(key, f"Used in calculation {cid}")

        if tool_name == "optimize_solar_storage" and result.mock:
            notes_desc = result.data.get("notes") or "Sample battery sizing for 8-hour backup; critical loads are not metered"
            self.assumptions.setdefault("A4", str(notes_desc))

        if tool_name == "search_ny_incentives_and_rules" and result.mock:
            self.assumptions.setdefault(
                "A5",
                "Incentive programs and rules from mock sample fixture, pending live verification",
            )

        if tool_name == "get_hazard_context" and result.mock:
            self.assumptions.setdefault(
                "A6",
                "Hazard ratings from mock sample fixture, pending site-specific assessment",
            )

    def summarize_for_llm(self) -> str:
        """
        Plain-text digest for the system/user context — keep it short to save tokens.

        Edit the template here if operators need more detail in the think step.
        """
        lines = ["## Fritts notes (working memory)"]
        if self.building_facts:
            lines.append(f"Building facts keys: {', '.join(sorted(self.building_facts.keys()))}")
        if self.calculation_runs:
            bits = []
            for cid, runs in sorted(self.calculation_runs.items()):
                shown = ", ".join(f"{run['value']} {run['units']}" for run in runs)
                bits.append(f"{cid} [{shown}]")
            lines.append("Calculations recorded: " + "; ".join(bits))
        if self.assumptions:
            lines.append("Assumptions: " + "; ".join(f"{k}: {v}" for k, v in self.assumptions.items()))
        if self.flags:
            lines.append("Flags: " + "; ".join(self.flags))
        if self.tool_calls:
            lines.append(f"Tools used so far ({len(self.tool_calls)}): " + ", ".join(t["tool"] for t in self.tool_calls))
        return "\n".join(lines)
