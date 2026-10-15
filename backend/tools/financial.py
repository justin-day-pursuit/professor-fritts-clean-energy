"""
Simple net cost and payback math for one package of measures (v5, tool run_financial_model).

This is NOT the full PySAM model (that comes later). Every output is an ESTIMATE shown as a
low-to-high range, built from the benchmark prices in COST_BENCHMARKS below. The agent never does
this arithmetic itself: it calls the tool, and the tool's calc_id (F-A, F-B, F-C) is what the plan cites.

To change a price or a savings percent, edit COST_BENCHMARKS / EFFICIENCY_LEVELS only. The assumption
text the agent quotes (A9) is built from the same tables, so the two can never disagree.
"""

from __future__ import annotations

from dataclasses import dataclass

# Benchmark prices as (low, high). These are planning-level ranges for NYC public buildings,
# not quotes: a real design and bid replaces them.
COST_BENCHMARKS = {
    "solar_usd_per_kw_dc": (3000.0, 4500.0),
    "battery_usd_per_kwh": (600.0, 1000.0),
}

# Efficiency packages: share of annual electricity saved, and cost per square foot of floor area.
# "standard" matches assumption A7 (LED and controls, 10-20%). "deep" adds envelope and HVAC work.
EFFICIENCY_LEVELS = {
    "none": {"savings_pct": (0.0, 0.0), "usd_per_sqft": (0.0, 0.0)},
    "standard": {"savings_pct": (10.0, 20.0), "usd_per_sqft": (4.0, 8.0)},
    "deep": {"savings_pct": (15.0, 25.0), "usd_per_sqft": (10.0, 16.0)},
}

# The federal commercial tax credit rate. It is applied only when the incentives tool reported the
# program as open; otherwise the plan leaves every incentive out of net cost (the safe default).
ITC_RATE = 0.30

# Share of a battery that can actually be used in an outage (the rest protects battery life).
BATTERY_USABLE_FRACTION = (0.85, 1.0)


def benchmark_assumption_text() -> str:
    """The one sentence behind assumption A9, built from the tables above."""
    std, deep = EFFICIENCY_LEVELS["standard"], EFFICIENCY_LEVELS["deep"]
    return (
        "Planning-level benchmark prices, not quotes: "
        f"solar ${COST_BENCHMARKS['solar_usd_per_kw_dc'][0]:,.0f}-{COST_BENCHMARKS['solar_usd_per_kw_dc'][1]:,.0f}/kW DC, "
        f"battery ${COST_BENCHMARKS['battery_usd_per_kwh'][0]:,.0f}-{COST_BENCHMARKS['battery_usd_per_kwh'][1]:,.0f}/kWh, "
        f"standard efficiency ${std['usd_per_sqft'][0]:.0f}-{std['usd_per_sqft'][1]:.0f}/sq ft saving "
        f"{std['savings_pct'][0]:.0f}-{std['savings_pct'][1]:.0f}%, "
        f"deep efficiency ${deep['usd_per_sqft'][0]:.0f}-{deep['usd_per_sqft'][1]:.0f}/sq ft saving "
        f"{deep['savings_pct'][0]:.0f}-{deep['savings_pct'][1]:.0f}%; "
        f"usable battery share {BATTERY_USABLE_FRACTION[0]:.0%}-{BATTERY_USABLE_FRACTION[1]:.0%}; "
        "the 30% federal credit counts only when the incentives tool says the program is open."
    )


@dataclass
class Package:
    """What one scenario installs. Sizes are already final (any budget cap was applied before this)."""

    efficiency_level: str = "none"
    solar_kw_dc: float = 0.0
    battery_kwh: float = 0.0


@dataclass
class Site:
    """Facts about the building and prices the math needs; all come from earlier tool results."""

    floor_area_sqft: float
    annual_use_kwh: float
    # Solar output of the FULL roof array, as a low/high pair; smaller arrays are scaled down in proportion.
    full_array_kw_dc: float
    full_array_kwh_low: float
    full_array_kwh_high: float
    price_low_usd_per_kwh: float
    price_high_usd_per_kwh: float
    budget_usd: float
    critical_load_kw: float = 0.0
    goal_fraction: float = 0.30
    federal_credit_open: bool = False


def _round_pair(low: float, high: float, digits: int = 0) -> list[float]:
    """Round a low/high pair for display; the list form keeps JSON output simple."""
    return [round(low, digits), round(high, digits)]


def model_package(package: Package, site: Site) -> dict:
    """
    Compute cost, savings, payback, budget strain and outage hours for one package.

    Ranges pair the cheap cost with the high benefit for the best case and the reverse for the worst,
    so a reader sees the full spread instead of a single number that sounds more certain than it is.
    """
    eff = EFFICIENCY_LEVELS[package.efficiency_level]

    # --- upfront cost (low, high) ---
    eff_cost = [site.floor_area_sqft * p for p in eff["usd_per_sqft"]]
    solar_cost = [package.solar_kw_dc * p for p in COST_BENCHMARKS["solar_usd_per_kw_dc"]]
    battery_cost = [package.battery_kwh * p for p in COST_BENCHMARKS["battery_usd_per_kwh"]]
    upfront = [eff_cost[i] + solar_cost[i] + battery_cost[i] for i in (0, 1)]

    # --- incentives: only the federal credit, only when confirmed open, only on solar and battery ---
    credit = [0.0, 0.0]
    if site.federal_credit_open:
        credit = [ITC_RATE * (solar_cost[i] + battery_cost[i]) for i in (0, 1)]
    # The credit grows with the solar and battery spend, so the low-cost case pairs with the low credit
    # and the high-cost case with the high credit. Low net is still the lowest net cost, high the highest.
    net = [upfront[0] - credit[0], upfront[1] - credit[1]]

    # --- energy: how many kWh per year the package removes from the grid bill ---
    efficiency_kwh = [site.annual_use_kwh * pct / 100.0 for pct in eff["savings_pct"]]
    scale = (package.solar_kw_dc / site.full_array_kw_dc) if site.full_array_kw_dc else 0.0
    solar_kwh = [site.full_array_kwh_low * scale, site.full_array_kwh_high * scale]
    # Solar and efficiency overlap slightly in real life (smaller load, same panels); adding them
    # slightly overstates the total, which is why every output stays a range with low confidence.
    reduction_kwh = [efficiency_kwh[i] + solar_kwh[i] for i in (0, 1)]
    reduction_pct = [100.0 * r / site.annual_use_kwh if site.annual_use_kwh else 0.0 for r in reduction_kwh]
    share_of_goal_pct = [100.0 * (p / 100.0) / site.goal_fraction for p in reduction_pct]

    # --- savings (USD per year) and simple payback (years) ---
    savings = [
        reduction_kwh[0] * site.price_low_usd_per_kwh,
        reduction_kwh[1] * site.price_high_usd_per_kwh,
    ]
    payback: list[float] | None = None
    if savings[0] > 0 and savings[1] > 0:
        # Fast payback = lowest net cost over highest savings; slow payback = the reverse.
        payback = [net[0] / savings[1], net[1] / savings[0]]

    # --- budget strain: upfront cost against the user's budget (credits arrive after the bill is paid) ---
    if site.budget_usd > 0:
        strain_ratio = [upfront[0] / site.budget_usd, upfront[1] / site.budget_usd]
        if upfront[1] <= site.budget_usd:
            strain = "within budget"
        elif upfront[0] <= site.budget_usd:
            strain = "may exceed budget"
        else:
            strain = "over budget"
    else:
        strain_ratio, strain = None, "no budget given"

    # --- outage hours: usable battery energy divided by the critical load ---
    if package.battery_kwh > 0 and site.critical_load_kw > 0:
        usable = [package.battery_kwh * f for f in BATTERY_USABLE_FRACTION]
        outage_hours = [usable[0] / site.critical_load_kw, usable[1] / site.critical_load_kw]
    else:
        # No battery: solar panels shut off in an outage, so there is no backup.
        outage_hours = [0.0, 0.0]

    return {
        "package": {
            "efficiency_level": package.efficiency_level,
            "solar_kw_dc": round(package.solar_kw_dc, 1),
            "battery_kwh": round(package.battery_kwh, 0),
        },
        "upfront_usd": _round_pair(*upfront),
        "incentives_counted_usd": _round_pair(*credit),
        "net_cost_usd": _round_pair(*net),
        "reduction_kwh": _round_pair(*reduction_kwh),
        "reduction_pct_of_use": _round_pair(*reduction_pct, 1),
        "share_of_goal_pct": _round_pair(*share_of_goal_pct, 0),
        "reaches_goal": reduction_pct[0] >= site.goal_fraction * 100.0,
        "annual_savings_usd": _round_pair(*savings),
        "payback_years": _round_pair(*payback, 1) if payback else None,
        "budget_strain": strain,
        "budget_ratio": _round_pair(*strain_ratio, 2) if strain_ratio else None,
        "outage_hours": _round_pair(*outage_hours, 1),
        "label": "ESTIMATE",
    }
