"""
Shared shape for every tool response — provenance fields plus optional flags.

The harness checks these fields in Check 3; mock fixtures must include the same keys.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
