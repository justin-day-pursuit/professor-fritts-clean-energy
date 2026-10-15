"""
Shared shape for every tool response — provenance fields plus optional flags.

The harness checks these fields in Check 3; mock fixtures must include the same keys.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolUnavailableError(RuntimeError):
    """
    A tool could not return data (API outage, HTTP error, or a saved fixture that records a failure).

    The harness catches this like any tool exception: the run keeps going, the failure is recorded
    in the notes, and the roadmap must say what is missing instead of inventing the numbers.
    """


class ToolResult(BaseModel):
    """One tool invocation result as the agent and run log store it."""

    tool: str
    data: dict[str, Any] = Field(default_factory=dict)
    source_url: str = ""
    retrieved_at: str = ""
    dataset_version: str = ""
    mock: bool = False
    stale: bool = False
    flags: list[str] = Field(default_factory=list)
