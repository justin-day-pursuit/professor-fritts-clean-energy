"""
Deterministic building-energy formulas C1–C4 for the calculate tool.

Each formula takes explicit numbers from the agent; results are labeled ESTIMATE in the harness.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from tools.base import ToolResult


class CalculateInput(BaseModel):
    """Inputs for one named formula (C1–C4)."""

    formula: str = Field(description="One of C1, C2, C3, C4")
    inputs: dict[str, float | int] = Field(default_factory=dict)
    assumption_ids: list[str] = Field(default_factory=list)


FORMULA_TEXT = {
    "C1": "usable_roof_sqft = roof_area_sqft × setback_factor",
    "C2": "array_kw_dc = usable_roof_sqft ÷ sqft_per_kw",
    "C3": "solar_offset_fraction = annual_solar_kwh ÷ annual_use_kwh",
    "C4": "annual_savings_usd = annual_solar_kwh × avg_rate_usd_per_kwh",
}


def run_calculate(payload: CalculateInput) -> ToolResult:
    """
    Run a single formula and return a ToolResult whose data holds value, units, and calc_id.

    Maintainers add new formulas here and register them in the tool docstring; keep each path pure math.
    """
    formula = payload.formula.strip().upper()
    inp = payload.inputs
    assumption_ids = list(payload.assumption_ids)

    if formula == "C1":
        roof = float(inp["roof_area_sqft"])
        factor = float(inp.get("setback_factor", 0.55))
        value = roof * factor
        units = "sq ft"
        calc_id = "C1"
    elif formula == "C2":
        usable = float(inp["usable_roof_sqft"])
        sqft_per_kw = float(inp.get("sqft_per_kw", 66))
        value = usable / sqft_per_kw
        units = "kW DC"
        calc_id = "C2"
    elif formula == "C3":
        solar_kwh = float(inp["annual_solar_kwh"])
        use_kwh = float(inp["annual_use_kwh"])
        value = solar_kwh / use_kwh if use_kwh else 0.0
        units = "fraction"
        calc_id = "C3"
    elif formula == "C4":
        solar_kwh = float(inp["annual_solar_kwh"])
        rate = float(inp["avg_rate_usd_per_kwh"])
        value = solar_kwh * rate
        units = "USD/yr"
        calc_id = "C4"
    else:
        raise ValueError(f"Unknown formula {formula!r}; use C1, C2, C3, or C4.")

    data: dict[str, Any] = {
        "calc_id": calc_id,
        "formula": FORMULA_TEXT[calc_id],
        "label": "ESTIMATE",
        "value": round(value, 4),
        "units": units,
        "inputs": dict(inp),
        "assumption_ids": assumption_ids,
    }
    return ToolResult(
        tool="calculate",
        data=data,
        source_url="internal://calculate",
        retrieved_at="",
        dataset_version="v0-code",
        mock=False,
    )
