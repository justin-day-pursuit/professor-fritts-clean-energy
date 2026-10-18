"""
The plan summary: everything a run found and calculated, organized for the screen (v7).

The roadmap text is written by the model. The numbers, records and sources behind it were produced by tools and by
code. This module gathers ALL of them into one structured block (run.output["summary"]) so the screen can show every
finding without reading markdown: nothing a tool returned is left out, it is only grouped.

The outcome (headline, tone) is decided here from the scenario numbers, not by the model, so the first thing a reader
sees always agrees with the figures. Every function is plain code with no Claude call.
"""

from __future__ import annotations

from typing import Any

from agent.plain_names import calculation_formula, calculation_name, tool_name
from tools.roof import plain_refusal

SUMMARY_VERSION = 3

# Plain-language text for each flag the tools raise. A flag with no entry is shown under its own name.
FLAG_TEXT = {
    "city_roof_not_solar_ready": "The city's own roof assessment says this roof is not solar ready. Check the roof, and consider replacing it, before solar.",
    "battery_inputs_estimated": "The battery size rests on an estimated critical load or backup length. Enter the real ones to resize it.",
    "statewide_average_rate": "Electricity prices are the New York average, not this building's own tariff. Confirm the tariff on a bill.",
    "tariff_needs_user_confirmation": "Which tariff the building is on has to be confirmed on a bill; none was chosen.",
    "hazard_partial": "Only the current FEMA flood zone was read. Heat and winter-storm ratings, and the 2015 preliminary flood map, were not checked.",
    "incentive_status_uncertain": "At least one incentive program could not be confirmed from its official page today, so it is left out of net cost.",
    "solar_price_placeholder": "The solar price is a placeholder because the NYC project-cost lookup was unavailable.",
    "battery_price_placeholder": "The battery price is a placeholder because the NYC project-cost lookup was unavailable.",
    "efficiency_price_placeholder": "The efficiency price is a placeholder because the NYC project-cost lookup was unavailable.",
    "address_street_mismatch": "The city's tax-lot record lists a different street than the one entered. Confirm the address.",
    "address_match_approximate": "The address match was approximate. Confirm the building is the right one.",
    "annual_kwh_from_bills": "Annual use was taken from the uploaded bills.",
    "budget_type_annual_not_modeled": "The budget is annual, but the model treats the amount as one total upfront figure.",
    "check4_partial": "The plan did not pass every quality check; read it as a partial plan.",
}
# The entries the city record can disagree with, in words.
MISMATCH_FIELD_LABELS = {
    "floor_area_sqft": "floor area",
    "roof_area_sqft": "roof area",
    "annual_kwh": "annual electricity use",
    "year_built": "year built",
}
MISSING_FIELD_LABELS = {
    "roof_replaced_year": "the year the roof was last replaced",
    "annual_kwh": "annual electricity use",
    "critical_loads": "the critical loads",
    "target_year": "the target year",
    "budget_year": "the budget year",
    "budget_type": "whether the budget is capital or annual",
    "existing_systems": "any solar or efficiency work already on the building",
    "utility": "the utility",
}


def _last_results(run: Any) -> dict[str, dict[str, Any]]:
    """The newest result of each tool in this run, as the stored payload (data, source, date, mock flag, flags)."""
    results: dict[str, dict[str, Any]] = {}
    for event in run.events.order_by("seq"):
        if event.kind == "tool_result" and isinstance(event.payload, dict) and event.payload.get("tool"):
            results[event.payload["tool"]] = event.payload
    return results


def _scenarios(calculations: dict[str, Any]) -> list[dict[str, Any]]:
    """Scenario A, B and C results, in order, exactly as the financial model produced them."""
    return [calculations[key] for key in ("F-A", "F-B", "F-C") if isinstance(calculations.get(key), dict)]


def _about(scenario: dict[str, Any]) -> str:
    """The cost as a range, with the median of similar NYC projects after it when there is one."""
    rng = _money(scenario.get("upfront_usd"))
    median = scenario.get("upfront_usd_best")
    if not median:
        return rng
    return f"{rng} (the median of similar NYC projects is about {_money([median, median]).split('-')[0]})"


def _money(pair: list[float] | None) -> str:
    """A low-high dollar range as text ($53k-$367k style for the headline)."""
    if not pair:
        return "n/a"

    def short(value: float) -> str:
        value = abs(value)
        return f"${value / 1_000_000:.2f}M" if value >= 1_000_000 else f"${value / 1000:,.0f}k"

    return f"{short(pair[0])}-{short(pair[1])}"


def decide_outcome(scenarios: list[dict[str, Any]], site_context: dict[str, Any], budget: float | None) -> dict[str, Any]:
    """
    The headline for the plan, decided from the numbers.

    needs_roof_check  a roof that is not flat and not verified: no solar was sized
    reached_within_budget  the cheapest scenario that reaches the goal at its low end and fits the budget
    reached_over_budget    a scenario reaches the goal but costs more than the budget
    close                  no scenario is sure, but at least one reaches the goal at its high end
    not_reached            no scenario reaches the goal
    partial                no scenario was calculated
    """
    if site_context.get("roof_kind") == "non_flat" and not site_context.get("verified_usable_roof_sqft"):
        return {
            "code": "needs_roof_check", "label": "Needs a roofer first", "tone": "next-step",
            "headline": "One step first: have the roof checked.",
            "subhead": "The roof is not flat, so solar is not sized until an engineer or roofer verifies the usable area.",
            "recommended": scenarios[0]["scenario_id"] if scenarios else None,
        }
    if not scenarios:
        return {"code": "partial", "label": "Partial plan", "tone": "caution",
                "headline": "This plan is incomplete.", "subhead": "No scenario could be calculated; see what to confirm first.",
                "recommended": None}
    goal = scenarios[0].get("goal_pct") or 30
    reaching = [s for s in scenarios if s.get("reaches_goal")]
    within = [s for s in reaching if s.get("budget_strain") == "within budget"]
    budget_text = f" your ${budget:,.0f} budget" if budget else " your budget"
    if within:
        best = min(within, key=lambda s: s["upfront_usd"][0])
        return {
            "code": "reached_within_budget", "label": "Goal reached within budget", "tone": "good",
            "headline": f"Yes. Plan {best['scenario_id']} reaches your {goal:g}% goal within{budget_text}.",
            "subhead": f"{best['scenario_name']}: cuts grid use {best['reduction_pct_of_use'][0]:g}-{best['reduction_pct_of_use'][1]:g}% "
                       f"for {_about(best)} before incentives.",
            "recommended": best["scenario_id"],
        }
    if reaching:
        best = min(reaching, key=lambda s: s["upfront_usd"][0])
        gap = best.get("budget_gap_usd")
        gap_text = f" and could cost up to {_money([gap[1], gap[1]]).split('-')[0]} more than{budget_text}" if gap and gap[1] > 0 else ""
        return {
            "code": "reached_over_budget", "label": "Goal reachable, over budget", "tone": "caution",
            "headline": f"Plan {best['scenario_id']} reaches your {goal:g}% goal{gap_text}.",
            "subhead": f"{best['scenario_name']}: cuts grid use {best['reduction_pct_of_use'][0]:g}-{best['reduction_pct_of_use'][1]:g}% "
                       f"for {_about(best)}. Reaching the goal may take more than the amount set aside.",
            "recommended": best["scenario_id"],
        }
    nearest = max(scenarios, key=lambda s: s["reduction_pct_of_use"][1])
    if nearest["reduction_pct_of_use"][1] >= goal:
        return {
            "code": "close", "label": "Close, but not certain", "tone": "caution",
            "headline": f"Close: {goal:g}% is within reach, but not certain.",
            "subhead": f"Plan {nearest['scenario_id']} cuts grid use {nearest['reduction_pct_of_use'][0]:g}-{nearest['reduction_pct_of_use'][1]:g}%, "
                       "so the goal is met only if savings land at the high end.",
            "recommended": nearest["scenario_id"],
        }
    return {
        "code": "not_reached", "label": "Goal not reached", "tone": "caution",
        "headline": f"No plan reaches {goal:g}%." if len(scenarios) < 3 else f"None of the three plans reaches {goal:g}%.",
        "subhead": f"The best, Plan {nearest['scenario_id']}, cuts grid use {nearest['reduction_pct_of_use'][0]:g}-{nearest['reduction_pct_of_use'][1]:g}%.",
        "recommended": nearest["scenario_id"],
    }


# What replacing a flat commercial roof costs in NYC, in dollars per square foot installed. The range is the span of the three
# membrane types in Roofvista's NYC guide (EPDM $6.50-11, TPO $8-13, modified bitumen $8-14), each including tear-off, insulation,
# membrane and flashing. These are contractor price guides, not audited project data, and Roofvista's page is written mainly for
# residential NYC buildings, so the figure is shown only as a labeled rough guide and never added to a total.
ROOF_REPLACEMENT_USD_PER_SQFT = (6.5, 14.0)
ROOF_REPLACEMENT_SOURCES = [
    {
        "label": "Roofvista, NYC flat roof replacement guide (published March 26, 2026): EPDM $6.50-11, TPO $8-13 and modified bitumen $8-14 per sq ft installed, including tear-off, insulation, membrane and flashing",
        "url": "https://roofvista.com/resources/guides/nyc-flat-roof-replacement-guide",
    },
    {
        "label": "Roof Observations, New York commercial roof costs (updated January 7, 2026): New York State averages of $5.45 to $24.30 per sq ft depending on membrane and insulation, and a note that New York City costs can run more than 50% above the national average",
        "url": "https://roofobservations.com/new-york-roof-cost-guide/",
    },
]


def not_included(profile: dict[str, Any], site: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Costs the plan's totals leave out, shown beside them so the reader is not surprised.

    Today: roof replacement, when the city or the user says the roof is old or poor. It is listed with a rough guide figure
    when the roof area is known, and always with the advice to get a roofer's quote.
    """
    items: list[dict[str, Any]] = []
    if site.get("roof_age_20_plus") or site.get("roof_condition") == "poor" or site.get("city_not_solar_ready"):
        try:
            area = float(profile.get("roof_area_sqft"))
        except (TypeError, ValueError):
            area = 0.0
        item: dict[str, Any] = {
            "item": "Replacing the roof, if it needs it",
            "why": "The roof is old or in poor shape, so it may need replacing before solar goes on. No plan's total includes this.",
            "next": "Get a roofer's quote.",
        }
        if area > 0:
            low, high = (round(area * p, -3) for p in ROOF_REPLACEMENT_USD_PER_SQFT)
            item["rough_guide_usd"] = [low, high]
            item["basis"] = (
                f"${ROOF_REPLACEMENT_USD_PER_SQFT[0]:.2f} to ${ROOF_REPLACEMENT_USD_PER_SQFT[1]:.2f} per sq ft installed, across "
                f"{area:,.0f} sq ft. That is the span of the three roof types in Roofvista's 2026 NYC guide (below). These are "
                "contractor price guides, not audited project data, and the NYC guide is written mainly for residential buildings, "
                "so treat the figure as a rough order of magnitude and get a roofer's quote."
            )
        item["sources"] = ROOF_REPLACEMENT_SOURCES
        items.append(item)
    return items


def _kw(value: Any) -> float | None:
    """A solar size in kW above zero, or None for blank, zero or text."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def confirm_first(
    flags: list[str],
    records: dict[str, Any],
    site: dict[str, Any],
    existing_solar_kw: Any = None,
    refusals: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """
    What the reader should check before relying on the plan, from the run's flags and the city-record differences.

    `refusals` holds, by tool name, the plain sentence for a tool that said no by a roof rule (see tools.roof.plain_refusal),
    so a deliberate "no room for new solar" is not reported as a lookup that could not return data.
    `existing_solar_kw` is the solar already on the roof as the user entered it, compared with the city's solar record.
    """
    refusals = refusals or {}
    existing = _kw(existing_solar_kw)
    items: list[dict[str, str]] = []
    for flag in flags:
        if flag.startswith("missing_field:"):
            name = flag.split(":", 1)[1]
            items.append({"kind": "missing", "text": f"Not given: {MISSING_FIELD_LABELS.get(name, name.replace('_', ' '))}. The plan states what it assumed."})
        elif flag.startswith("intake_mismatch:"):
            field = flag.split(":", 1)[1]
            diff = next((d for d in records.get("differs_from_intake", []) if d.get("field") == field), {})
            detail = f" You entered {diff.get('intake'):,.0f}; the city record says {diff.get('city_record'):,.0f}." if diff.get("intake") and diff.get("city_record") else ""
            items.append({"kind": "mismatch", "text": f"Your {MISMATCH_FIELD_LABELS.get(field, field.replace('_', ' '))} differs from the city record.{detail}"})
        elif flag.startswith("tool_error:"):
            name = flag.split(":", 1)[1]
            if name in refusals:
                items.append({"kind": "flag", "text": refusals[name]})
            else:
                items.append({"kind": "gap", "text": f"{tool_name(name)} could not return data, so that part of the plan is missing."})
        elif flag == "city_roof_not_solar_ready" and existing:
            items.append(
                {
                    "kind": "flag",
                    "text": "The city's roof assessment rates this roof not solar ready, yet solar is already installed. Check the roof's condition, and who owns the array, before relying on this plan.",
                }
            )
        elif flag in FLAG_TEXT:
            items.append({"kind": "flag", "text": FLAG_TEXT[flag]})
    # Solar already on the roof: the size the user entered against the size in the city's solar record.
    ll24 = records.get("ll24") or {}
    # Only completed solar is compared: a planned array is not on the roof, so a smaller entered size is not a conflict.
    city_kw = _kw(ll24.get("installed_kw")) if str(ll24.get("status") or "").strip().lower() == "completed" else None
    if existing and city_kw and abs(existing - city_kw) > 0.1 * max(existing, city_kw):
        items.append(
            {
                "kind": "mismatch",
                "text": f"The solar already on the roof differs from the city's solar record. You entered {existing:g} kW; the city's record says {city_kw:g} kW. Confirm which is right, and who owns the array.",
            }
        )
    if not_included({}, site):
        items.append({"kind": "flag", "text": "No plan's cost includes replacing the roof, which may be needed first. Get a roofer's quote."})
    if site.get("roof_age_20_plus") and "city_roof_not_solar_ready" not in flags:
        items.append({"kind": "flag", "text": "The city lists the roof as 20 years old or more. Check it before solar."})
    return items


def _roof_refusals(run: Any) -> dict[str, str]:
    """For each tool the run called that a roof rule turned down, the plain sentence saying why (read from the run's error events)."""
    reasons: dict[str, str] = {}
    for event in run.events.all():
        if event.kind != "error":
            continue
        tool = event.payload.get("tool")
        reason = plain_refusal(event.payload.get("message"))
        if tool and reason:
            reasons[str(tool)] = reason
    return reasons


def build_plan_summary(run: Any, output: dict[str, Any], next_steps: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """
    Gather everything the run found and calculated into one structured block.

    The solar, price, battery and hazard entries are each tool's whole stored result (data plus source, date and the
    live-or-sample flag), so the screen can say where the numbers came from; the other parts hold plain data.

    `output` is the run output being assembled (roadmap payload, notes). Nothing is dropped: the full roadmap sections,
    every calculation, every tool result's data, its source and date, and the notes' assumptions, flags and links are
    all present, grouped by topic.
    """
    notes = output.get("notes") or {}
    roadmap = output.get("roadmap") or {}
    results = _last_results(run)
    data = {tool: (payload.get("data") or {}) for tool, payload in results.items()}
    calculations = notes.get("calculations") or {}
    site = notes.get("site_context") or {}
    flags = list(notes.get("flags") or [])
    profile = (data.get("get_building_profile") or {}).get("profile") or {}
    records = data.get("lookup_ny_building_records") or {}
    scenarios = _scenarios(calculations)
    try:
        budget = float(profile.get("budget_amount")) if profile.get("budget_amount") else None
    except (TypeError, ValueError):
        budget = None

    ll84 = records.get("ll84") or {}
    annual_kwh = profile.get("annual_kwh")
    if profile.get("annual_kwh_source") == "bills":
        kwh_source = "uploaded bills"
    elif ll84.get("electricity_kwh") and annual_kwh and abs(float(annual_kwh) - ll84["electricity_kwh"]) <= 0.25 * ll84["electricity_kwh"]:
        kwh_source = "your entry, matching the city's Local Law 84 report"
    elif annual_kwh:
        kwh_source = "your entry"
    else:
        kwh_source = "benchmark (no figure given)"
    goal_pct = profile.get("goal_percent") or (scenarios[0].get("goal_pct") if scenarios else None)

    cost_basis = {
        key: {"price": scenarios[-1].get(price_key), "basis": scenarios[-1].get(basis_key), "source_url": scenarios[-1].get(url_key)}
        for key, price_key, basis_key, url_key in (
            ("solar", "solar_usd_per_kw", "solar_price_basis", "solar_price_source_url"),
            ("battery", "battery_usd_per_kwh", "battery_price_basis", "battery_price_source_url"),
            ("efficiency", "efficiency_usd_per_kwh", "efficiency_price_basis", "efficiency_price_source_url"),
        )
    } if scenarios else {}
    if scenarios:
        cost_basis["efficiency_savings_realization"] = scenarios[-1].get("efficiency_realization")
        cost_basis["assumption_text"] = scenarios[-1].get("assumption_text")

    sections = roadmap.get("sections") or []
    referrals = next((s.get("claims", []) for s in sections if s.get("section_id") == "10"), [])

    return {
        "version": SUMMARY_VERSION,
        "plain_answer": (roadmap.get("plain_answer") or "").strip() or None,
        "outcome": decide_outcome(scenarios, site, budget),
        "building": {
            "intake": profile,
            "city_records": records,
            "energy_report": ll84 or None,
            "roof_assessment": records.get("ll24"),
            "site_context": site,
        },
        "baseline": {
            "annual_kwh": annual_kwh,
            "source": kwh_source,
            "goal_percent": goal_pct,
            "goal_kwh": round(float(annual_kwh) * float(goal_pct) / 100) if annual_kwh and goal_pct else None,
        },
        "solar": {"production": results.get("get_solar_production") or None},
        "prices": {"electricity": results.get("get_utility_rates") or None, "tariff": results.get("get_utility_tariff") or None},
        "scenarios": scenarios,
        "not_included": not_included(profile, site),
        "cost_basis": cost_basis,
        "incentives": (data.get("search_ny_incentives_and_rules") or {}).get("programs") or [],
        "battery": results.get("optimize_solar_storage") or None,
        "hazards": results.get("get_hazard_context") or None,
        "calculations": {
            key: {**value, "name": calculation_name(key), "plain_formula": calculation_formula(key)}
            for key, value in calculations.items()
            if not key.startswith("F-")
        },
        "calculation_names": {key: calculation_name(key) for key in ("C1", "C2", "C3", "C4", "F-A", "F-B", "F-C")},
        "flag_text": FLAG_TEXT,
        "confirm_first": confirm_first(flags, records, site, profile.get("existing_solar_kw"), _roof_refusals(run)),
        "assumptions": [{"id": key, "text": text} for key, text in (notes.get("assumptions") or {}).items()],
        "referrals": referrals,
        "next_steps": next_steps or [],
        "sources": (notes.get("source_links") or [])
        + (
            [{"label": f"Contractor price guide, not audited: {g['label'].split(':')[0]}", "url": g["url"], "retrieved_at": "2026-10-17T00:00:00Z", "sample": False} for g in ROOF_REPLACEMENT_SOURCES]
            if not_included(profile, site)
            else []
        ),
        "sections": sections,
        "flags": flags,
        "tools": [
            {
                "tool": tool,
                "mock": payload.get("mock"),
                "source_url": payload.get("source_url"),
                "retrieved_at": payload.get("retrieved_at"),
                "dataset_version": payload.get("dataset_version"),
                "flags": payload.get("flags") or [],
            }
            for tool, payload in results.items()
        ],
        "usage": (run.flags or {}).get("usage") if getattr(run, "flags", None) else None,
    }
