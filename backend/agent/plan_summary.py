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

SUMMARY_VERSION = 1

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
                       f"for {_money(best['upfront_usd'])} before incentives.",
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
                       f"for {_money(best['upfront_usd'])}. Reaching the goal may take more than the amount set aside.",
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
        "headline": f"None of the three plans reaches {goal:g}%.",
        "subhead": f"The best, Plan {nearest['scenario_id']}, cuts grid use {nearest['reduction_pct_of_use'][0]:g}-{nearest['reduction_pct_of_use'][1]:g}%.",
        "recommended": nearest["scenario_id"],
    }


def confirm_first(flags: list[str], records: dict[str, Any], site: dict[str, Any]) -> list[dict[str, str]]:
    """What the reader should check before relying on the plan, from the run's flags and the city-record differences."""
    items: list[dict[str, str]] = []
    for flag in flags:
        if flag.startswith("missing_field:"):
            name = flag.split(":", 1)[1]
            items.append({"kind": "missing", "text": f"Not given: {MISSING_FIELD_LABELS.get(name, name.replace('_', ' '))}. The plan states what it assumed."})
        elif flag.startswith("intake_mismatch:"):
            field = flag.split(":", 1)[1]
            diff = next((d for d in records.get("differs_from_intake", []) if d.get("field") == field), {})
            detail = f" You entered {diff.get('intake'):,.0f}; the city record says {diff.get('city_record'):,.0f}." if diff.get("intake") and diff.get("city_record") else ""
            items.append({"kind": "mismatch", "text": f"Your {field.replace('_', ' ')} differs from the city record.{detail}"})
        elif flag.startswith("tool_error:"):
            items.append({"kind": "gap", "text": f"{flag.split(':', 1)[1]} could not return data, so that part is missing."})
        elif flag in FLAG_TEXT:
            items.append({"kind": "flag", "text": FLAG_TEXT[flag]})
    if site.get("roof_age_20_plus") and "city_roof_not_solar_ready" not in flags:
        items.append({"kind": "flag", "text": "The city lists the roof as 20 years old or more. Check it before solar."})
    return items


def build_plan_summary(run: Any, output: dict[str, Any], next_steps: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """
    Gather everything the run found and calculated into one structured block.

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
        "solar": {"production": data.get("get_solar_production") or None},
        "prices": {"electricity": data.get("get_utility_rates") or None, "tariff": data.get("get_utility_tariff") or None},
        "scenarios": scenarios,
        "cost_basis": cost_basis,
        "incentives": (data.get("search_ny_incentives_and_rules") or {}).get("programs") or [],
        "battery": data.get("optimize_solar_storage") or None,
        "hazards": data.get("get_hazard_context") or None,
        "calculations": {key: value for key, value in calculations.items() if not key.startswith("F-")},
        "confirm_first": confirm_first(flags, records, site),
        "assumptions": [{"id": key, "text": text} for key, text in (notes.get("assumptions") or {}).items()],
        "referrals": referrals,
        "next_steps": next_steps or [],
        "sources": notes.get("source_links") or [],
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
