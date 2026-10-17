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
from tools.roof import check_roof_sizing_allowed, roof_kind, verified_usable_area
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
            "Size a battery for the critical loads from the user's own critical load kW and backup hours (estimated and flagged when blank; saved sample only in mock mode). Returns battery_kwh, "
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
            "Flood context for the address: live mode reads the current FEMA flood zone (heat and storm ratings are "
            "not looked up); mock mode returns saved sample ratings."
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


def _check_roof_formula(formula: str, inputs: dict[str, Any], profile: dict[str, Any]) -> None:
    """
    v6: keep the flat-roof formulas off a roof that is not flat.

    C1 and C2 size the usable roof and the array from flat-roof defaults. For a pitched, tower, dome or
    mixed roof they are refused until the intake has a usable area verified by an engineer or roofer. Once it
    does, C1 must be run on that verified area with no setback (setback_factor 1), so the plan cites the
    verified number and not the flat-roof guess.
    """
    if formula.strip().upper() not in ("C1", "C2") or roof_kind(profile.get("roof_type")) != "non_flat":
        return
    check_roof_sizing_allowed(profile)
    verified = verified_usable_area(profile) or 0.0
    if formula.strip().upper() == "C1":
        area = float(inputs.get("roof_area_sqft", 0))
        setback = float(inputs.get("setback_factor", 0.55))
        if abs(area - verified) > 0.5 or abs(setback - 1.0) > 1e-9:
            raise ValueError(
                f"This roof is not flat and its usable area was verified at {verified:,.0f} sq ft. "
                f"Run C1 with roof_area_sqft={verified:,.0f} and setback_factor=1."
            )


def _with_saved_price_ranges(inp: Any, fixture_case: str) -> Any:
    """
    Replays: price the scenarios with the real ranges saved next to a recorded case (cost_ranges.json), so a free
    replay shows the same dollar figures the live run did. Cases with no such file keep the placeholder prices.
    """
    import json

    from mocks.catalog import FIXTURES_ROOT

    path = FIXTURES_ROOT / fixture_case / "cost_ranges.json"
    if not path.exists():
        return inp
    saved = json.loads(path.read_text(encoding="utf-8"))
    update: dict[str, Any] = {}
    solar, battery, efficiency = saved.get("solar"), saved.get("battery"), saved.get("efficiency")
    if solar and not inp.solar_usd_per_kw_low:
        update.update(solar_usd_per_kw_low=solar["low"], solar_usd_per_kw_high=solar["high"],
                      solar_price_basis=solar["basis"], solar_price_source_url=solar.get("source_url") or "")
    if battery and inp.battery_kwh > 0 and not inp.battery_usd_per_kwh_low:
        update.update(battery_usd_per_kwh_low=battery["low"], battery_usd_per_kwh_high=battery["high"],
                      battery_price_basis=battery["basis"], battery_price_source_url=battery.get("source_url") or "")
    if saved.get("realization") and not inp.efficiency_realization:
        update.update(efficiency_realization=saved["realization"])
    if efficiency and not inp.efficiency_usd_per_kwh:
        update.update(efficiency_usd_per_kwh=efficiency["prices"], efficiency_price_basis=efficiency["basis"],
                      efficiency_price_source_url=efficiency.get("source_url") or "")
    return inp.model_copy(update=update) if update else inp


def _with_real_solar_price(inp: Any, fixture_case: str = "") -> tuple[Any, list[str]]:
    """
    In live mode, replace the placeholder solar price with real NYC project costs (NYSERDA data, tools/solar_costs.py).

    The model's solar range becomes the 25th to 75th percentile cost per kW of comparable completed projects.
    If the lookup fails or has too few projects, the placeholder stays and a flag says so. Mock mode is left alone
    so saved demos replay with the same numbers.
    """
    from mocks.mock_mode import get_tool_mode
    from tools.solar_costs import SolarCostError, fetch_solar_cost_range

    if get_tool_mode() != "live":
        return (_with_saved_price_ranges(inp, fixture_case) if fixture_case else inp), []
    flags: list[str] = []
    if not inp.solar_usd_per_kw_low:
        inp, solar_flags = _with_real_solar_only(inp)
        flags += solar_flags
    if inp.battery_kwh > 0 and not inp.battery_usd_per_kwh_low:
        inp, battery_flags = _with_real_battery_price(inp)
        flags += battery_flags
    if not inp.efficiency_usd_per_kwh:
        inp, efficiency_flags = _with_real_efficiency_price(inp)
        flags += efficiency_flags
    if not inp.efficiency_realization:
        from tools.financial import EFFICIENCY_REALIZATION

        inp = inp.model_copy(update={"efficiency_realization": list(EFFICIENCY_REALIZATION)})
    return inp, flags


def _with_real_efficiency_price(inp: Any) -> tuple[Any, list[str]]:
    """Fill the efficiency cost per kWh saved from NYSERDA's completed NYC projects; keep the placeholder (flagged) if unavailable."""
    from tools.efficiency_costs import EfficiencyCostError, fetch_efficiency_cost_ranges

    try:
        found = fetch_efficiency_cost_ranges()
    except EfficiencyCostError:
        found = None
    if not found:
        return inp, ["efficiency_price_placeholder"]
    standard, deep = found["standard"], found["deep"]
    basis = (
        f"25th-75th percentile of {standard['projects']} LED-lighting and {deep['projects']} comprehensive completed "
        f"NYC public-sector projects since {found['since']}, NYSERDA data {found['source_url']}"
    )
    return inp.model_copy(update={
        "efficiency_usd_per_kwh": {"standard": [standard["p25"], standard["p75"]], "deep": [deep["p25"], deep["p75"]]},
        "efficiency_price_basis": basis,
        "efficiency_price_source_url": found["source_url"],
    }), []


def _with_real_battery_price(inp: Any) -> tuple[Any, list[str]]:
    """Fill the battery price from NYSERDA's NYC storage projects; keep the placeholder (and flag it) if unavailable."""
    from tools.solar_costs import SolarCostError, fetch_storage_cost_range

    try:
        found = fetch_storage_cost_range()
    except SolarCostError:
        found = None
    if not found:
        return inp, ["battery_price_placeholder"]
    basis = (
        f"25th-75th percentile of {found['projects']} completed or approved NYC commercial-scale storage projects, "
        f"NYSERDA data {found['source_url']}"
    )
    return inp.model_copy(update={
        "battery_usd_per_kwh_low": float(found["p25_usd_per_kwh"]),
        "battery_usd_per_kwh_high": float(found["p75_usd_per_kwh"]),
        "battery_price_basis": basis,
        "battery_price_source_url": found["source_url"],
    }), []


def _with_real_solar_only(inp: Any) -> tuple[Any, list[str]]:
    """Fill the solar price from NYSERDA's NYC projects; keep the placeholder (and flag it) if unavailable."""
    from tools.solar_costs import SolarCostError, fetch_solar_cost_range

    try:
        found = fetch_solar_cost_range(inp.full_array_kw_dc)
    except SolarCostError:
        found = None
    if not found:
        return inp, ["solar_price_placeholder"]
    low, high = found["band_kw"]
    basis = (
        f"25th-75th percentile of {found['projects']} completed NYC non-residential projects of "
        f"{low:g}-{high:g} kW since {found['since'][:4]}, NYSERDA data {found['source_url']}"
    )
    updated = inp.model_copy(update={
        "solar_price_source_url": found["source_url"],
        "solar_usd_per_kw_low": float(found["p25_usd_per_kw"]),
        "solar_usd_per_kw_high": float(found["p75_usd_per_kw"]),
        "solar_price_basis": basis,
    })
    return updated, []


def _goal_fraction_from_profile(profile: dict[str, Any]) -> float | None:
    """The intake's goal percent (5 to 100) as a fraction, or None when it is blank or not a usable number."""
    try:
        pct = float(profile.get("goal_percent"))
    except (TypeError, ValueError):
        return None
    return pct / 100.0 if 0 < pct <= 100 else None


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
        return optimize_solar_storage(fixture_case, session_profile)
    if name == "calculate":
        _check_roof_formula(validated.formula, validated.inputs, session_profile)
        calc_in = CalculateInput(
            formula=validated.formula,
            inputs=dict(validated.inputs),
            assumption_ids=list(validated.assumption_ids),
        )
        return run_calculate(calc_in)
    if name == "run_financial_model":
        # The user's own goal percent decides the goal, not whatever number the model passes.
        goal_pct = _goal_fraction_from_profile(session_profile)
        if goal_pct is not None:
            validated = validated.model_copy(update={"goal_fraction": goal_pct})
        validated, price_flags = _with_real_solar_price(validated, fixture_case)
        result = run_financial_model(validated)
        if price_flags:
            result = result.model_copy(update={"flags": list(result.flags) + price_flags})
        return result
    if name == "get_utility_rates":
        return get_utility_rates(fixture_case, session_profile)
    if name == "get_utility_tariff":
        return get_utility_tariff(fixture_case, session_profile)
    if name == "search_ny_incentives_and_rules":
        return search_ny_incentives_and_rules(fixture_case, session_profile)
    if name == "get_hazard_context":
        return get_hazard_context(fixture_case, session_profile)
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
