"""
The three planning scenarios (v5) and the code that sizes them.

  A  efficiency only
  B  efficiency + solar, sized to stay within the user's budget
  C  the full path to the goal: deep efficiency + the whole roof array + a backup battery

The model does not size anything itself. It calls run_financial_model once per scenario id and cites
the calc_id that comes back (F-A, F-B, F-C). This file decides what each scenario contains; the
arithmetic lives in tools/financial.py.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from tools.base import ToolResult
from tools.financial import (
    COST_BENCHMARKS,
    EFFICIENCY_LEVELS,
    Package,
    Site,
    benchmark_assumption_text,
    model_package,
)

SCENARIO_NAMES = {
    "A": "Efficiency only",
    "B": "Efficiency + solar within budget",
    "C": "Full path to the goal (deep efficiency + full solar + backup battery)",
}


class FinancialModelInput(BaseModel):
    """What the agent sends to run_financial_model; every value comes from an earlier tool result."""

    scenario_id: str = Field(description="A, B or C")
    floor_area_sqft: float = Field(gt=0)
    annual_use_kwh: float = Field(gt=0, description="Annual grid use in kWh (measured or the A8 benchmark)")
    budget_usd: float = Field(ge=0, description="The user's budget; 0 if none was given")
    full_array_kw_dc: float = Field(gt=0, description="Array size that fits the free roof: C2, or free_capacity_kw from get_solar_production when the roof already has solar")
    annual_solar_kwh_low: float = Field(ge=0, description="Low end of solar output for the whole-roof array")
    annual_solar_kwh_high: float = Field(ge=0, description="High end of solar output for the whole-roof array")
    price_low_usd_per_kwh: float = Field(gt=0)
    price_high_usd_per_kwh: float = Field(gt=0)
    battery_kwh: float = Field(default=0, ge=0, description="Battery size from optimize_solar_storage; used by scenario C only")
    critical_load_kw: float = Field(default=0, ge=0, description="Critical load from optimize_solar_storage")
    goal_fraction: float = Field(default=0.30, gt=0, le=1, description="Reduction goal as a fraction, 0.30 for 30%")
    solar_usd_per_kw_low: float | None = Field(default=None, gt=0, description="Set by the system from real NYC project costs; leave blank")
    solar_usd_per_kw_high: float | None = Field(default=None, gt=0, description="Set by the system from real NYC project costs; leave blank")
    solar_price_basis: str = Field(default="", description="Set by the system; where the solar price came from")
    solar_price_source_url: str = Field(default="", description="Set by the system; web page of the solar price data")
    battery_usd_per_kwh_low: float | None = Field(default=None, gt=0, description="Set by the system from real NYC project costs; leave blank")
    battery_usd_per_kwh_high: float | None = Field(default=None, gt=0, description="Set by the system from real NYC project costs; leave blank")
    battery_price_basis: str = Field(default="", description="Set by the system; where the battery price came from")
    battery_price_source_url: str = Field(default="", description="Set by the system; web page of the battery price data")
    federal_credit_open: bool = Field(
        default=False,
        description="True ONLY if search_ny_incentives_and_rules reported the federal credit as open",
    )


def build_package(scenario_id: str, inp: FinancialModelInput) -> Package:
    """Decide what scenario A, B or C installs, applying the budget cap to B."""
    sid = scenario_id.strip().upper()
    if sid == "A":
        return Package(efficiency_level="standard")
    if sid == "B":
        # Spend on efficiency first, then put whatever budget is left into solar. The worst-case
        # (high) prices are used so the scenario stays within budget even if costs come in high.
        eff_cost_high = inp.floor_area_sqft * EFFICIENCY_LEVELS["standard"]["usd_per_sqft"][1]
        left = max(0.0, inp.budget_usd - eff_cost_high) if inp.budget_usd > 0 else 0.0
        high_price = inp.solar_usd_per_kw_high or COST_BENCHMARKS["solar_usd_per_kw_dc"][1]
        affordable_kw = left / high_price
        return Package(efficiency_level="standard", solar_kw_dc=min(inp.full_array_kw_dc, affordable_kw))
    if sid == "C":
        return Package(
            efficiency_level="deep",
            solar_kw_dc=inp.full_array_kw_dc,
            battery_kwh=inp.battery_kwh,
        )
    raise ValueError(f"Unknown scenario {scenario_id!r}; use A, B or C.")


def run_financial_model(inp: FinancialModelInput) -> ToolResult:
    """Run one scenario and return a ToolResult whose data carries the calc_id (F-A, F-B or F-C)."""
    sid = inp.scenario_id.strip().upper()
    if inp.annual_solar_kwh_low > inp.annual_solar_kwh_high:
        raise ValueError("annual_solar_kwh_low must not be above annual_solar_kwh_high.")
    if inp.price_low_usd_per_kwh > inp.price_high_usd_per_kwh:
        raise ValueError("price_low_usd_per_kwh must not be above price_high_usd_per_kwh.")
    # Scenario C promises backup power. A missing battery or critical load would quietly report zero
    # outage hours, so refuse the input and tell the agent what to fetch instead.
    if sid == "C" and (inp.battery_kwh <= 0 or inp.critical_load_kw <= 0):
        raise ValueError(
            "Scenario C needs battery_kwh and critical_load_kw above 0. "
            "Call optimize_solar_storage first and pass its battery_kwh and critical_load_kw."
        )
    package = build_package(sid, inp)
    site = Site(
        floor_area_sqft=inp.floor_area_sqft,
        annual_use_kwh=inp.annual_use_kwh,
        full_array_kw_dc=inp.full_array_kw_dc,
        full_array_kwh_low=inp.annual_solar_kwh_low,
        full_array_kwh_high=inp.annual_solar_kwh_high,
        price_low_usd_per_kwh=inp.price_low_usd_per_kwh,
        price_high_usd_per_kwh=inp.price_high_usd_per_kwh,
        budget_usd=inp.budget_usd,
        critical_load_kw=inp.critical_load_kw,
        goal_fraction=inp.goal_fraction,
        federal_credit_open=inp.federal_credit_open,
        solar_usd_per_kw=(
            (inp.solar_usd_per_kw_low, inp.solar_usd_per_kw_high)
            if inp.solar_usd_per_kw_low and inp.solar_usd_per_kw_high
            else None
        ),
        solar_price_basis=inp.solar_price_basis,
        battery_usd_per_kwh=(
            (inp.battery_usd_per_kwh_low, inp.battery_usd_per_kwh_high)
            if inp.battery_usd_per_kwh_low and inp.battery_usd_per_kwh_high
            else None
        ),
        battery_price_basis=inp.battery_price_basis,
    )
    result = model_package(package, site)

    # Solar alone, whole roof: the number that shows rooftop solar cannot reach the goal by itself.
    solar_alone = [
        round(100.0 * inp.annual_solar_kwh_low / inp.annual_use_kwh, 1),
        round(100.0 * inp.annual_solar_kwh_high / inp.annual_use_kwh, 1),
    ]
    data = {
        "calc_id": f"F-{sid}",
        "scenario_id": sid,
        "scenario_name": SCENARIO_NAMES[sid],
        "solar_alone_pct_of_use": solar_alone,
        "solar_alone_reaches_goal": solar_alone[0] >= inp.goal_fraction * 100.0,
        # Solar sized for the whole roof can out-produce the building's use (v6); the part above 100% is surplus.
        "solar_alone_exceeds_use": solar_alone[1] > 100.0,
        "goal_pct": inp.goal_fraction * 100.0,
        "assumption_text": benchmark_assumption_text(
            site.solar_usd_per_kw, inp.solar_price_basis, site.battery_usd_per_kwh, inp.battery_price_basis
        ),
        "solar_usd_per_kw": [inp.solar_usd_per_kw_low, inp.solar_usd_per_kw_high] if inp.solar_usd_per_kw_low else None,
        "battery_usd_per_kwh": [inp.battery_usd_per_kwh_low, inp.battery_usd_per_kwh_high] if inp.battery_usd_per_kwh_low else None,
        "solar_price_basis": inp.solar_price_basis or None,
        "solar_price_source_url": inp.solar_price_source_url or None,
        "battery_price_basis": inp.battery_price_basis or None,
        "battery_price_source_url": inp.battery_price_source_url or None,
        **result,
    }
    return ToolResult(
        tool="run_financial_model",
        data=data,
        source_url="internal://run_financial_model",
        # Computed now, from inputs that already carry their own sources, so the run time is the honest date.
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version="v5-simple-payback",
        mock=False,
    )
