"""
Central registry of tools the v0 agent may call, with Pydantic input schemas.

Not registered in v0 (listed here for the roadmap only):
  run_financial_model, search_evidence, upsert_reference_cache
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from tools.base import ToolResult
from tools.building_records import get_building_profile, lookup_ny_building_records
from tools.calculate import CalculateInput, run_calculate
from tools.climate_risk import get_hazard_context
from tools.ny_rules_rates import get_utility_rates, search_ny_incentives_and_rules
from tools.solar_savings import get_solar_production, optimize_solar_storage

ToolHandler = Callable[..., ToolResult]


class EmptyInput(BaseModel):
    """Tools that need no arguments beyond session context."""

    pass


class LookupBuildingInput(BaseModel):
    address: str | None = None


class CalculateToolInput(BaseModel):
    formula: str
    inputs: dict[str, float | int] = Field(default_factory=dict)
    assumption_ids: list[str] = Field(default_factory=list)


class ToolSpec(BaseModel):
    """Metadata the LLM and Check 2 use to validate a call."""

    name: str
    description: str
    input_model: type[BaseModel]
    freshness_kind: str = "default"
    group: int = 0


TOOL_SPECS: dict[str, ToolSpec] = {
    "get_building_profile": ToolSpec(
        name="get_building_profile",
        description="Read the user's intake profile for this session.",
        input_model=EmptyInput,
        freshness_kind="default",
        group=1,
    ),
    "lookup_ny_building_records": ToolSpec(
        name="lookup_ny_building_records",
        description="Look up public building records in New York (mock in v0).",
        input_model=LookupBuildingInput,
        freshness_kind="building_records",
        group=1,
    ),
    "get_solar_production": ToolSpec(
        name="get_solar_production",
        description="Estimate rooftop solar production (mock PVWatts in v0).",
        input_model=EmptyInput,
        freshness_kind="solar_production",
        group=2,
    ),
    "optimize_solar_storage": ToolSpec(
        name="optimize_solar_storage",
        description="Size battery for critical loads (mock REopt in v0).",
        input_model=EmptyInput,
        freshness_kind="solar_production",
        group=2,
    ),
    "calculate": ToolSpec(
        name="calculate",
        description="Run formulas C1–C4 on explicit numeric inputs.",
        input_model=CalculateToolInput,
        freshness_kind="default",
        group=2,
    ),
    "get_utility_rates": ToolSpec(
        name="get_utility_rates",
        description="Commercial electric tariff for the site (mock in v0).",
        input_model=EmptyInput,
        freshness_kind="utility_rates",
        group=3,
    ),
    "search_ny_incentives_and_rules": ToolSpec(
        name="search_ny_incentives_and_rules",
        description="NY and federal incentives and permit rules (mock in v0).",
        input_model=EmptyInput,
        freshness_kind="incentives",
        group=3,
    ),
    "get_hazard_context": ToolSpec(
        name="get_hazard_context",
        description="Heat and flood exposure context (mock FEMA in v0).",
        input_model=EmptyInput,
        freshness_kind="hazard",
        group=4,
    ),
}


def list_tool_names() -> list[str]:
    """Names of tools Check 2 may approve."""
    return sorted(TOOL_SPECS.keys())


def get_tool_spec(name: str) -> ToolSpec | None:
    return TOOL_SPECS.get(name)


def validate_tool_input(name: str, raw: dict[str, Any]) -> BaseModel:
    """Parse and validate tool arguments; raises ValidationError on bad input."""
    spec = TOOL_SPECS.get(name)
    if spec is None:
        raise KeyError(name)
    return spec.input_model.model_validate(raw or {})


def execute_tool(
    name: str,
    raw_input: dict[str, Any],
    *,
    session_profile: dict[str, Any],
    fixture_case: str,
) -> ToolResult:
    """
    Dispatch one registered tool — the harness calls this after Check 2 passes.

    Session profile and fixture_case come from the Django Session row.
    """
    validated = validate_tool_input(name, raw_input)
    if name == "get_building_profile":
        return get_building_profile(session_profile)
    if name == "lookup_ny_building_records":
        addr = getattr(validated, "address", None)
        return lookup_ny_building_records(fixture_case, address=addr)
    if name == "get_solar_production":
        return get_solar_production(fixture_case)
    if name == "optimize_solar_storage":
        return optimize_solar_storage(fixture_case)
    if name == "calculate":
        calc_in = CalculateInput(
            formula=validated.formula,
            inputs=dict(validated.inputs),
            assumption_ids=list(validated.assumption_ids),
        )
        return run_calculate(calc_in)
    if name == "get_utility_rates":
        return get_utility_rates(fixture_case)
    if name == "search_ny_incentives_and_rules":
        return search_ny_incentives_and_rules(fixture_case)
    if name == "get_hazard_context":
        return get_hazard_context(fixture_case)
    raise KeyError(f"Tool {name!r} is not implemented.")
