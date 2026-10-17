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

# Share of an audit's predicted efficiency savings that the City's measured projects actually delivered: "gross
# savings realizations rates range from 62% to 88%" in the past three Local Law 87 annual reports (DCAS, FY2022 report,
# section 3, footnote 9). Applied in live runs only; see EFFICIENCY_REALIZATION_SOURCE.
EFFICIENCY_REALIZATION = (0.62, 0.88)
EFFICIENCY_REALIZATION_URL = (
    "https://www.nyc.gov/assets/dcas/downloads/pdf/energy/reportsandpublication/local-law-87-annual-report-fy-2022.pdf"
)
EFFICIENCY_REALIZATION_SOURCE = (
    f"NYC DCAS Local Law 87 annual report FY2022, section 3 (city projects realized 62-88% of predicted savings), "
    f"{EFFICIENCY_REALIZATION_URL}"
)

# The federal commercial tax credit rate. It is applied only when the incentives tool reported the
# program as open; otherwise the plan leaves every incentive out of net cost (the safe default).
ITC_RATE = 0.30

# Share of a battery that can actually be used in an outage (the rest protects battery life).
BATTERY_USABLE_FRACTION = (0.85, 1.0)


def efficiency_cost_range(
    level: str,
    floor_area_sqft: float,
    annual_use_kwh: float,
    real_prices: dict[str, tuple[float, float]] | None = None,
) -> tuple[float, float]:
    """
    Low and high upfront cost of an efficiency package.

    With real prices (dollars per kWh saved per year, from NYSERDA's completed projects) the cost is the kWh the
    package saves times that price: the low end pairs the low savings with the 25th percentile price, the high end
    the high savings with the 75th percentile price. Without them it falls back to the placeholder dollars per
    square foot.
    """
    eff = EFFICIENCY_LEVELS[level]
    if real_prices and level in real_prices:
        saved = [annual_use_kwh * pct / 100.0 for pct in eff["savings_pct"]]
        return (saved[0] * real_prices[level][0], saved[1] * real_prices[level][1])
    return (floor_area_sqft * eff["usd_per_sqft"][0], floor_area_sqft * eff["usd_per_sqft"][1])


def benchmark_assumption_text(
    solar_price: tuple[float, float] | None = None,
    solar_basis: str = "",
    battery_price: tuple[float, float] | None = None,
    battery_basis: str = "",
    efficiency_prices: dict[str, tuple[float, float]] | None = None,
    efficiency_basis: str = "",
    realization: tuple[float, float] | None = None,
) -> str:
    """
    The one sentence behind assumption A9, built from the tables above.

    When real solar prices were found (solar_price, with solar_basis naming the source) the sentence quotes them
    instead of the placeholder range, so the plan says where the solar price came from.
    """
    std, deep = EFFICIENCY_LEVELS["standard"], EFFICIENCY_LEVELS["deep"]
    solar = solar_price or COST_BENCHMARKS["solar_usd_per_kw_dc"]
    solar_text = f"solar ${solar[0]:,.0f}-{solar[1]:,.0f}/kW DC" + (f" ({solar_basis})" if solar_basis else " (planning estimate)")
    battery = battery_price or COST_BENCHMARKS["battery_usd_per_kwh"]
    if efficiency_prices:
        efficiency_text = (
            f"efficiency cost per kWh saved per year ${efficiency_prices['standard'][0]:.2f}-{efficiency_prices['standard'][1]:.2f} "
            f"(standard) and ${efficiency_prices['deep'][0]:.2f}-{efficiency_prices['deep'][1]:.2f} (deep) ({efficiency_basis}), "
        )
    else:
        efficiency_text = (
            f"standard efficiency ${std['usd_per_sqft'][0]:.0f}-{std['usd_per_sqft'][1]:.0f}/sq ft and "
            f"deep efficiency ${deep['usd_per_sqft'][0]:.0f}-{deep['usd_per_sqft'][1]:.0f}/sq ft (planning estimates), "
        )
    battery_text = f"battery ${battery[0]:,.0f}-{battery[1]:,.0f}/kWh" + (
        f" ({battery_basis})" if battery_basis else " (planning estimate)"
    )
    return (
        "Planning-level benchmark prices, not quotes: "
        f"{solar_text}, "
        f"{battery_text}, "
        f"{efficiency_text}"
        f"standard efficiency saving "
        f"{std['savings_pct'][0]:.0f}-{std['savings_pct'][1]:.0f}%, "
        f"deep efficiency saving "
        f"{deep['savings_pct'][0]:.0f}-{deep['savings_pct'][1]:.0f}%; "
        f"usable battery share {BATTERY_USABLE_FRACTION[0]:.0%}-{BATTERY_USABLE_FRACTION[1]:.0%}; "
        "the efficiency savings percents are planning estimates, not yet backed by project data"
        + (
            f", but only {realization[0]:.0%}-{realization[1]:.0%} of them is counted because the City's audited "
            f"projects delivered that share ({EFFICIENCY_REALIZATION_SOURCE})"
            if realization
            else ""
        )
        + ("; " if efficiency_prices else ", and so are the efficiency prices; ")
        + 
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
    # Solar price per kW DC as (low, high). Real project costs replace the placeholder when they were found.
    solar_usd_per_kw: tuple[float, float] | None = None
    # Where that price came from, quoted in the itemized bill; blank means the placeholder was used.
    solar_price_basis: str = ""
    # Battery price per kWh as (low, high); real NYC project costs replace the placeholder when found.
    battery_usd_per_kwh: tuple[float, float] | None = None
    battery_price_basis: str = ""
    # Efficiency cost per kWh saved per year by level ({"standard": (low, high), "deep": (low, high)}); real project
    # costs replace the placeholder dollars per square foot when found.
    efficiency_usd_per_kwh: dict[str, tuple[float, float]] | None = None
    efficiency_price_basis: str = ""
    # Share of the predicted efficiency savings that is really delivered, as (low, high); None means all of it.
    efficiency_realization: tuple[float, float] | None = None


def _round_pair(low: float, high: float, digits: int = 0) -> list[float]:
    """Round a low/high pair for display; the list form keeps JSON output simple."""
    return [round(low, digits), round(high, digits)]


def _budget_note(strain: str, gap: list[float] | None, reaches_goal: bool) -> str:
    """
    One plain sentence about the budget for this scenario, quoted in the plan.

    When the package costs more than the budget, it says by how much and whether it reaches the goal, and
    that extending the budget is a choice for the user.
    """
    if gap is None:
        return "No budget was given, so budget strain was not assessed."
    if strain == "within budget":
        return "The estimated cost fits within the budget."
    low, high = gap
    amount = f"${low:,.0f}-${high:,.0f}" if low > 0 else f"up to ${high:,.0f}"
    if reaches_goal:
        return (
            f"Reaches the goal, but the estimated cost is {amount} more than your budget. Reaching the goal may take "
            "more than the amount set aside; compare that gap with the savings before deciding whether to extend it."
        )
    return f"The estimated cost is {amount} more than your budget, and it does not reach the goal at the low end."


def model_package(package: Package, site: Site) -> dict:
    """
    Compute cost, savings, payback, budget strain and outage hours for one package.

    Ranges pair the cheap cost with the high benefit for the best case and the reverse for the worst,
    so a reader sees the full spread instead of a single number that sounds more certain than it is.
    """
    eff = EFFICIENCY_LEVELS[package.efficiency_level]

    # --- upfront cost (low, high) ---
    eff_cost = list(efficiency_cost_range(
        package.efficiency_level, site.floor_area_sqft, site.annual_use_kwh, site.efficiency_usd_per_kwh
    ))
    solar_price = site.solar_usd_per_kw or COST_BENCHMARKS["solar_usd_per_kw_dc"]
    solar_cost = [package.solar_kw_dc * p for p in solar_price]
    battery_price = site.battery_usd_per_kwh or COST_BENCHMARKS["battery_usd_per_kwh"]
    battery_cost = [package.battery_kwh * p for p in battery_price]
    upfront = [eff_cost[i] + solar_cost[i] + battery_cost[i] for i in (0, 1)]

    # --- incentives: only the federal credit, only when confirmed open, only on solar and battery ---
    credit = [0.0, 0.0]
    if site.federal_credit_open:
        credit = [ITC_RATE * (solar_cost[i] + battery_cost[i]) for i in (0, 1)]
    # The credit grows with the solar and battery spend, so the low-cost case pairs with the low credit
    # and the high-cost case with the high credit. Low net is still the lowest net cost, high the highest.
    net = [upfront[0] - credit[0], upfront[1] - credit[1]]

    # --- energy: how many kWh per year the package removes from the grid bill ---
    realization = site.efficiency_realization or (1.0, 1.0)
    efficiency_kwh = [site.annual_use_kwh * pct / 100.0 * realization[i] for i, pct in enumerate(eff["savings_pct"])]
    scale = (package.solar_kw_dc / site.full_array_kw_dc) if site.full_array_kw_dc else 0.0
    solar_kwh = [site.full_array_kwh_low * scale, site.full_array_kwh_high * scale]
    # Solar can only replace power the building still uses after efficiency. Anything beyond that is surplus
    # that flows to the grid (v6): it is shown to the user as potential but never counted as a bill saving,
    # because export credits depend on net-metering rules this model does not check. This keeps every
    # reduction at or below 100% of annual use, so a plan never claims to cut more than the building uses.
    use_after_efficiency = [max(site.annual_use_kwh - efficiency_kwh[i], 0.0) for i in (0, 1)]
    solar_used_kwh = [min(solar_kwh[i], use_after_efficiency[i]) for i in (0, 1)]
    surplus_kwh = [solar_kwh[i] - solar_used_kwh[i] for i in (0, 1)]
    # Solar and efficiency overlap slightly in real life (smaller load, same panels); adding them
    # slightly overstates the total, which is why every output stays a range with low confidence.
    reduction_kwh = [efficiency_kwh[i] + solar_used_kwh[i] for i in (0, 1)]
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

    # --- budget gap: how much more than the budget the package costs (v6) ---
    # A plan that reaches the goal can still need more money than the user set aside. The gap says so in
    # dollars, so the user can weigh extending the budget against the savings instead of discarding the option.
    reaches_goal = reduction_pct[0] >= site.goal_fraction * 100.0
    if site.budget_usd > 0:
        gap = [max(upfront[0] - site.budget_usd, 0.0), max(upfront[1] - site.budget_usd, 0.0)]
    else:
        gap = None
    budget_note = _budget_note(strain, gap, reaches_goal)

    # --- outage hours: usable battery energy divided by the critical load ---
    if package.battery_kwh > 0 and site.critical_load_kw > 0:
        usable = [package.battery_kwh * f for f in BATTERY_USABLE_FRACTION]
        outage_hours = [usable[0] / site.critical_load_kw, usable[1] / site.critical_load_kw]
    else:
        # No battery: solar panels shut off in an outage, so there is no backup.
        outage_hours = [0.0, 0.0]

    # The itemized bill: each line is what it costs at the low and high price, and what the price is based on.
    cost_items: list[dict] = []
    if package.efficiency_level != "none":
        cost_items.append({
            "item": f"{package.efficiency_level.title()} efficiency package",
            "basis": (
                f"{site.annual_use_kwh * eff['savings_pct'][0] / 100:,.0f}-{site.annual_use_kwh * eff['savings_pct'][1] / 100:,.0f} kWh "
                f"saved a year (planning estimate {eff['savings_pct'][0]:.0f}-{eff['savings_pct'][1]:.0f}%) x "
                f"${site.efficiency_usd_per_kwh[package.efficiency_level][0]:.2f}-{site.efficiency_usd_per_kwh[package.efficiency_level][1]:.2f} "
                f"per kWh saved ({site.efficiency_price_basis})"
                if site.efficiency_usd_per_kwh and package.efficiency_level in site.efficiency_usd_per_kwh
                else f"{site.floor_area_sqft:,.0f} sq ft x ${eff['usd_per_sqft'][0]:.0f}-{eff['usd_per_sqft'][1]:.0f}/sq ft (planning estimate)"
            ),
            "usd": _round_pair(*eff_cost),
        })
    if package.solar_kw_dc > 0:
        cost_items.append({
            "item": "Rooftop solar",
            "basis": f"{package.solar_kw_dc:,.1f} kW DC x ${solar_price[0]:,.0f}-{solar_price[1]:,.0f}/kW"
            + (f" ({site.solar_price_basis})" if site.solar_price_basis else " (planning estimate)"),
            "usd": _round_pair(*solar_cost),
        })
    if package.battery_kwh > 0:
        cost_items.append({
            "item": "Backup battery",
            "basis": f"{package.battery_kwh:,.0f} kWh x ${battery_price[0]:,.0f}-{battery_price[1]:,.0f}/kWh"
            + (f" ({site.battery_price_basis})" if site.battery_price_basis else " (planning estimate)"),
            "usd": _round_pair(*battery_cost),
        })
    if credit[1] > 0:
        cost_items.append({
            "item": "Federal credit (30% of solar and battery)",
            "basis": "Counted only because the incentives tool reported the program open",
            "usd": _round_pair(-credit[0], -credit[1]),
        })

    return {
        "cost_items": cost_items,
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
        "reaches_goal": reaches_goal,
        "surplus_solar_kwh": _round_pair(*surplus_kwh),
        "surplus_not_counted_in_savings": surplus_kwh[1] > 0,
        "budget_gap_usd": _round_pair(*gap) if gap else None,
        "budget_note": budget_note,
        "annual_savings_usd": _round_pair(*savings),
        "payback_years": _round_pair(*payback, 1) if payback else None,
        "budget_strain": strain,
        "budget_ratio": _round_pair(*strain_ratio, 2) if strain_ratio else None,
        "outage_hours": _round_pair(*outage_hours, 1),
        "label": "ESTIMATE",
    }
