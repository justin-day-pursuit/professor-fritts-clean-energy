"""Verify successful repeat tool calls are not blocked by the retry limit."""

from __future__ import annotations

from agent.checks import run_check2
from agent.limits import RunLimits


def test_four_successful_calculate_calls_allowed():
    limits = RunLimits()
    for _ in range(4):
        result = run_check2(
            "calculate",
            {"formula": "C1", "inputs": {"roof_area_sqft": 1000, "setback_factor": 0.55}},
            limits,
        )
        assert result["passed"]
        limits.record_successful_tool_call("calculate")
    assert limits.tool_call_count == 4
    assert limits.failed_attempts_by_tool.get("calculate", 0) == 0
