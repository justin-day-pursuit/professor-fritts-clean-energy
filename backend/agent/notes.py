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
        if tool_name == "calculate" and "calc_id" in result.data:
            cid = result.data["calc_id"]
            self.calculations[cid] = result.data
            for aid in result.data.get("assumption_ids") or []:
                key = str(aid)
                self.assumptions.setdefault(key, f"Used in calculation {cid}")

    def summarize_for_llm(self) -> str:
        """
        Plain-text digest for the system/user context — keep it short to save tokens.

        Edit the template here if operators need more detail in the think step.
        """
        lines = ["## Fritts notes (working memory)"]
        if self.building_facts:
            lines.append(f"Building facts keys: {', '.join(sorted(self.building_facts.keys()))}")
        if self.calculations:
            lines.append(f"Calculations recorded: {', '.join(sorted(self.calculations.keys()))}")
        if self.assumptions:
            lines.append("Assumptions: " + "; ".join(f"{k}: {v}" for k, v in self.assumptions.items()))
        if self.flags:
            lines.append("Flags: " + "; ".join(self.flags))
        if self.tool_calls:
            lines.append(f"Tools used so far ({len(self.tool_calls)}): " + ", ".join(t["tool"] for t in self.tool_calls))
        return "\n".join(lines)
