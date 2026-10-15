"""
Central registry of tools the agent may call, with Pydantic input schemas.

Registered from v5: run_financial_model (simple payback, scenarios A/B/C).
Not registered yet (listed here for the roadmap only):
  search_evidence
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from agent.scenarios import FinancialModelInput, run_financial_model
from tools.base import ToolResult
from tools.building_records import get_building_profile, lookup_ny_building_records
from tools.calculate import CalculateInput, describe_formulas, run_calculate
from tools.climate_risk import get_hazard_context
from tools.ny_rules_rates import get_utility_rates, get_utility_tariff, search_ny_incentives_and_rules
from tools.solar_savings import get_solar_production, optimize_solar_storage
from tools.upsert_cache import upsert_reference_cache as _upsert_cache_handler

ToolHandler = Callable[..., ToolResult]


class EmptyInput(BaseModel):
    """Tools that need no arguments beyond session context."""

    pass


class LookupBuildingInput(BaseModel):
    address: str | None = None


class CalculateToolInput(BaseModel):
    formula: str = Field(description="One of C1, C2, C3, C4")
    inputs: dict[str, float | int] = Field(
        default_factory=dict,
        description="Numbers for the formula, using exactly the input names in this tool's description.",
    )
    assumption_ids: list[str] = Field(default_factory=list)


class SolarProductionInput(BaseModel):
    """Optional array size in kW DC; left out, the tool sizes it from the roof area."""

    system_kw: float | None = Field(default=None, gt=0)


# run_financial_model takes the scenario sizing inputs defined next to the scenarios themselves.
FinancialModelToolInput = FinancialModelInput

class UpsertCacheInput(BaseModel):
    """Arguments for the upsert_reference_cache write tool."""

    record_id: str = Field(description="Stable key, e.g. 'incentive:nyserda-clean-green-schools'")
    payload: dict[str, Any] = Field(
        description="The data to cache (status, deadline, eligibility, quoted text)",
    )
    source_url: str = Field(description="Official page URL the data was retrieved from")
    retrieved_at: str = Field(default="", description="ISO 8601 retrieval timestamp")
    page_hash: str = Field(default="", description="SHA-256 of the raw page content")
    freshness_kind: str = Field(default="incentives", description="Cache freshness category")


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
        description="Look up public building records in New York (live NYC Open Data in live mode, saved records in mock mode).",
        input_model=LookupBuildingInput,
        freshness_kind="building_records",
        group=1,
    ),
    "get_solar_production": ToolSpec(
        name="get_solar_production",
        description=(
            "Estimate rooftop solar production (live PVWatts in live mode, saved PVWatts in mock mode). "
            "Pass system_kw from C2 when you have it. If you omit it, the tool sizes the array "
            "with the same defaults as C1 and C2 (setback 0.55, 66 sq ft per kW)."
        ),
        input_model=SolarProductionInput,
        freshness_kind="solar_production",
        group=2,
    ),
    "optimize_solar_storage": ToolSpec(
        name="optimize_solar_storage",
        description=(
            "Size a battery for the critical loads (saved REopt sample data until v8). Returns battery_kwh, "
            "battery_kw and critical_load_kw; pass those to run_financial_model for scenario C."
        ),
        input_model=EmptyInput,
        freshness_kind="solar_production",
        group=2,
    ),
    "calculate": ToolSpec(
        name="calculate",
        description="Run one deterministic formula on explicit numbers. " + describe_formulas(),
        input_model=CalculateToolInput,
        freshness_kind="default",
        group=2,
    ),
    "run_financial_model": ToolSpec(
        name="run_financial_model",
        description=(
            "Simple net cost, payback, budget strain and outage hours for ONE scenario: A (efficiency only), "
            "B (efficiency + solar within budget) or C (deep efficiency + full solar + battery). Call it once per "
            "scenario with the SAME site inputs. The tool does the sizing and arithmetic; cite its calc_id "
            "(F-A, F-B, F-C). All outputs are ESTIMATE ranges; this is a simple payback, not the full SAM model."
        ),
        input_model=FinancialModelToolInput,
        freshness_kind="default",
        group=2,
    ),
    "get_utility_rates": ToolSpec(
        name="get_utility_rates",
        description="Commercial electricity price for the site (live EIA New York average in live mode, saved tariff in mock mode).",
        input_model=EmptyInput,
        freshness_kind="utility_rates",
        group=3,
    ),
    "get_utility_tariff": ToolSpec(
        name="get_utility_tariff",
        description=(
            "Named utility tariff with effective date and energy/demand charge ranges "
            "(saved OpenEI-style sample data until v8; flagged for the user to confirm)."
        ),
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
        description=(
            "Heat, flood, and winter-storm context from saved FEMA and NYC flood data "
            "(mock until a later version; not a live FEMA call)."
        ),
        input_model=EmptyInput,
        freshness_kind="hazard",
        group=4,
    ),
    "upsert_reference_cache": ToolSpec(
        name="upsert_reference_cache",
        description=(
            "Save a fresh result to the versioned cache. Only accepts data from approved "
            "official sources. Returns the version number and a changed flag. Changes that "
            "make a plan more cautious save automatically; more favorable changes save as "
            "'pending' until a person confirms."
        ),
        input_model=UpsertCacheInput,
        freshness_kind="default",
        group=5,
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
        return lookup_ny_building_records(fixture_case, address=addr, profile=session_profile)
    if name == "get_solar_production":
        return get_solar_production(fixture_case, session_profile, getattr(validated, "system_kw", None))
    if name == "optimize_solar_storage":
        return optimize_solar_storage(fixture_case)
    if name == "calculate":
        calc_in = CalculateInput(
            formula=validated.formula,
            inputs=dict(validated.inputs),
            assumption_ids=list(validated.assumption_ids),
        )
        return run_calculate(calc_in)
    if name == "run_financial_model":
        return run_financial_model(validated)
    if name == "get_utility_rates":
        return get_utility_rates(fixture_case, session_profile)
    if name == "get_utility_tariff":
        return get_utility_tariff(fixture_case)
    if name == "search_ny_incentives_and_rules":
        return search_ny_incentives_and_rules(fixture_case)
    if name == "get_hazard_context":
        return get_hazard_context(fixture_case)
    if name == "upsert_reference_cache":
        return _upsert_cache_handler(
            record_id=validated.record_id,
            payload=validated.payload,
            source_url=validated.source_url,
            retrieved_at=validated.retrieved_at,
            page_hash=validated.page_hash,
            freshness_kind=validated.freshness_kind,
        )
    raise KeyError(f"Tool {name!r} is not implemented.")
