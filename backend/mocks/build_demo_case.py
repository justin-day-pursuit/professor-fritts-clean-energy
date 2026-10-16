"""
Build the demo case folder for P.S. 236 Langston Hughes (DOE building X173), 1871 Walton Avenue, Bronx.

Real data, pulled Oct 16, 2026 from free public APIs: NYC PLUTO, NYC building footprints, PVWatts v8, EIA prices, FEMA's flood
map, plus a hand-checked snapshot of incentives and rules read from official pages the same day. The tariff and the battery
sizing are still saved samples, and the plan says so. The plan text in scripted_llm.json is written by us from the real tool
numbers (no Claude call), so it is a SCRIPTED plan, not a recording; record_case replaces it after a live run.

Run from backend/ with the venv python:  python mocks/build_demo_case.py
It reads the saved live pulls already in mocks/fixtures/demo_ps236_bronx/ (building records, solar, prices) and rewrites the
intake, the hazard and incentive snapshots, the scripted plan and expected.json. To refresh the data, re-pull those three files
first and re-read the incentive pages (the snapshot goes stale after 7 days), then update the quotes below.
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fritts.settings")
sys.path.insert(0, str(Path.cwd()))
import django

django.setup()
from agent.scenarios import FinancialModelInput, run_financial_model
from tools.calculate import CalculateInput, run_calculate

SP = Path(sys.argv[1]) if len(sys.argv) > 1 else None
FIX = Path.cwd() / "mocks" / "fixtures"
CASE = "demo_ps236_bronx"
FOLDER = FIX / CASE
FOLDER.mkdir(exist_ok=True)
RETRIEVED = "2026-10-16T15:00:00Z"
PROFILE = "session://profile"


def write(name, obj):
    (FOLDER / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def c(text, label, confidence, **kw):
    claim = {"text": text, "label": label, "confidence": confidence}
    claim.update({k: v for k, v in kw.items() if v is not None})
    return claim


def rng(low, high, units):
    return {"value_low": low, "value_high": high, "units": units}


def n(x):
    return f"{x:,.0f}"


def calc(formula, inputs):
    return run_calculate(CalculateInput(formula=formula, inputs=inputs)).data


def tool(name, inp=None):
    return {"type": "tool", "name": name, "input": inp or {}}


# ---------------------------------------------------------------------------------------------- intake
intake = {
    "_comment": (
        "Real building: P.S. 236 Langston Hughes (DOE building X173), 1871 Walton Avenue, Bronx, BBL 2028510021. Public data: LL84 2024 "
        "(kWh 456,834, floor area 43,760, built 1994), PLUTO (DOE-owned, 4 floors, no landmark), building footprints (one outline, 10,255 sq ft "
        "= the suggested roof area), FEMA effective flood map (zone X, minimal hazard). STATED CHOICES, not public: the $800,000 capital budget "
        "and its year, the critical loads, the 'none' answers for existing systems, and the flat roof (not checked on aerial imagery). "
        "roof_replaced_year is left blank on purpose."
    ),
    "contact_name": "Facilities manager",
    "building_name": "P.S. 236 Langston Hughes (DOE building X173)",
    "address": "1871 Walton Avenue", "borough": "Bronx", "city": "New York", "state": "NY",
    "building_type": "elementary school", "floor_area_sqft": 43760, "year_built": 1994,
    "roof_type": "flat", "roof_area_sqft": 10260, "utility": "Con Edison", "annual_kwh": 456834,
    "budget_amount": 800000, "budget_year": 2027, "budget_type": "capital",
    "goal": "Cut grid electricity 30% by 2030", "target_year": 2030,
    "critical_loads": "emergency lighting and communications",
    "existing_renewables": "none", "existing_efficiency": "none",
    "question": "How can our school cut grid electricity 30% by 2030 on an $800,000 capital budget?",
}
write("intake.json", intake)

# ------------------------------------------------------------------------------------- real tool answers
if SP is not None:  # first build: copy the live pulls in; later builds keep the ones already in the folder
    for tool_name in ("lookup_ny_building_records", "get_utility_rates", "get_solar_production"):
        shutil.copy(SP / f"ps236_{tool_name}.json", FOLDER / f"{tool_name}.json")
rec = json.loads((FOLDER / "lookup_ny_building_records.json").read_text(encoding="utf-8"))
solar = json.loads((FOLDER / "get_solar_production.json").read_text(encoding="utf-8"))
rates = json.loads((FOLDER / "get_utility_rates.json").read_text(encoding="utf-8"))

# Flood hazard: the real FEMA effective zone for this site; heat and storm ratings were not looked up.
write("get_hazard_context.json", {
    "retrieved_at": RETRIEVED, "dataset_version": "fema-nfhl-effective-2026-10-16", "mock": False, "stale": False,
    "source_url": "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer",
    "tool": "get_hazard_context",
    "data": {
        "flood_zone": "X", "zone_subtype": "AREA OF MINIMAL FLOOD HAZARD", "flood_rating": "minimal",
        "notes": "FEMA National Flood Hazard Layer, effective map, point lookup at the school (40.8489, -73.9095). Heat and winter-storm ratings were not looked up.",
    },
    "flags": [],
})

# Incentives and rules: a hand-checked snapshot of official pages, read on 2026-10-16. Every quote is exact.
def page_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

q_irs = "Tax-exempt and governmental entities can benefit from certain clean energy investment and production credits using new options enabled by legislation enacted in 2022."
q_stat = "shall not apply to any qualified property placed in service by the taxpayer after December 31, 2027"
q_dcas = "86 more public school solar projects, totaling 17.2 MW, are actively in progress."
q_dob = "a solar photovoltaic system, a green roof system, or a combination of the two"
write("search_ny_incentives_and_rules.json", {
    "retrieved_at": RETRIEVED, "dataset_version": "hand-checked-official-pages-2026-10-16", "mock": False, "stale": False,
    "source_url": "https://www.irs.gov/credits-deductions/elective-pay-and-transferability",
    "tool": "search_ny_incentives_and_rules",
    "data": {
        "_comment": "Snapshot read by hand from official pages on 2026-10-16. Not a live reader: it goes stale after 7 days under the freshness rule.",
        "programs": [
            {
                "name": "Federal elective pay (direct pay) for governmental entities, solar investment credit (IRC 6417 / 48E)",
                "status": "open", "deadline": "2027-12-31",
                "deadline_note": "Solar property must be placed in service by 2027-12-31 (statute, 26 U.S.C. 48E(e)(4)(A), for facilities whose construction begins after 2026-07-04).",
                "quote": q_irs, "statute_quote": q_stat,
                "source_url": "https://www.irs.gov/credits-deductions/elective-pay-and-transferability",
                "statute_url": "https://www.law.cornell.edu/uscode/text/26/48E",
                "page_hash": page_hash(q_irs), "page_last_updated": "2026-06-27", "retrieved_at": RETRIEVED,
            },
            {
                "name": "NYC Solar Schools program (DCAS, NYPA, NYC Public Schools): rooftop solar on DOE schools under power purchase agreements",
                "status": "uncertain",
                "status_note": "Ongoing: 130 installations done (27.5 MW) and 86 more in progress as of 2026-04-23. The release describes no enrollment process, and it is not known whether this building is in the pipeline.",
                "quote": q_dcas,
                "source_url": "https://www.nyc.gov/site/dcas/news/010-26/nycps-dcas-complete-130-solar-installations-city-school-roofs-latest-completion-marie",
                "page_hash": page_hash(q_dcas), "retrieved_at": RETRIEVED,
            },
            {
                "name": "NYSERDA NY-Sun commercial and industrial solar incentive (Con Edison region)",
                "status": "uncertain",
                "status_note": "Current block status could not be confirmed from an official page on 2026-10-16: NYSERDA's dashboard blocked automated access. A March 2026 NYSERDA update was found only through search results and could not be read.",
                "source_url": "https://www.nyserda.ny.gov/All-Programs/NY-Sun/Contractors/Dashboards-and-incentives/ConEd-Dashboard",
                "retrieved_at": RETRIEVED,
            },
            {
                "name": "NYC Local Laws 92 and 94 of 2019 (sustainable roofs): rule, not an incentive",
                "status": "rule",
                "status_note": "Applies to new buildings and existing buildings undergoing certain major roof renovations; the roof must have a solar photovoltaic system, a green roof system, or both, over any applicable roof.",
                "quote": q_dob,
                "source_url": "https://www.nyc.gov/site/buildings/dob/pr-sustainable-roof-requirements.page",
                "page_hash": page_hash(q_dob), "page_date": "2019-11-15", "retrieved_at": RETRIEVED,
            },
        ],
    },
    "flags": [],
})
# The tariff and battery sizing are still saved samples (copied from case 1, flagged as samples).
for name in ("get_utility_tariff", "optimize_solar_storage"):
    shutil.copy(FIX / "case1_queens_library" / f"{name}.json", FOLDER / f"{name}.json")
battery = json.loads((FOLDER / "optimize_solar_storage.json").read_text(encoding="utf-8"))["data"]

# --------------------------------------------------------------------------------------------- numbers
roof = intake["roof_area_sqft"]
c1 = calc("C1", {"roof_area_sqft": roof, "setback_factor": 0.55})
c2 = calc("C2", {"usable_roof_sqft": c1["value"]})
kw = solar["data"]["system_kw_dc"]
sd = solar["data"]
use = intake["annual_kwh"]
p_low, p_high = rates["data"]["price_low_usd_per_kwh"], rates["data"]["price_high_usd_per_kwh"]
c3 = calc("C3", {"annual_solar_kwh": sd["annual_ac_kwh"], "annual_use_kwh": use})
c4_low = calc("C4", {"annual_solar_kwh": sd["annual_ac_kwh_low"], "avg_rate_usd_per_kwh": p_low})
c4_high = calc("C4", {"annual_solar_kwh": sd["annual_ac_kwh_high"], "avg_rate_usd_per_kwh": p_high})
site = dict(
    floor_area_sqft=intake["floor_area_sqft"], annual_use_kwh=use, budget_usd=intake["budget_amount"], full_array_kw_dc=kw,
    annual_solar_kwh_low=sd["annual_ac_kwh_low"], annual_solar_kwh_high=sd["annual_ac_kwh_high"],
    price_low_usd_per_kwh=p_low, price_high_usd_per_kwh=p_high, critical_load_kw=battery["critical_load_kw"], federal_credit_open=True,
)
fin = {}
fin_steps = []
for sid in "ABC":
    inp = dict(site, scenario_id=sid, battery_kwh=battery["battery_kwh"] if sid == "C" else 0)
    fin[sid] = run_financial_model(FinancialModelInput(**inp)).data
    fin_steps.append(tool("run_financial_model", inp))
A, B, C = fin["A"], fin["B"], fin["C"]

steps = [
    {"type": "think", "message": "Reviewing the intake for P.S. 236 and the question."},
    tool("get_building_profile"),
    tool("lookup_ny_building_records", {"address": intake["address"]}),
    tool("calculate", {"formula": "C1", "inputs": {"roof_area_sqft": roof, "setback_factor": 0.55}}),
    tool("calculate", {"formula": "C2", "inputs": {"usable_roof_sqft": c1["value"]}}),
    tool("get_solar_production", {"system_kw": kw}),
    tool("get_utility_rates"),
    tool("get_utility_tariff"),
    tool("calculate", {"formula": "C3", "inputs": {"annual_solar_kwh": sd["annual_ac_kwh"], "annual_use_kwh": use}}),
    tool("calculate", {"formula": "C4", "inputs": {"annual_solar_kwh": sd["annual_ac_kwh_low"], "avg_rate_usd_per_kwh": p_low}}),
    tool("calculate", {"formula": "C4", "inputs": {"annual_solar_kwh": sd["annual_ac_kwh_high"], "avg_rate_usd_per_kwh": p_high}}),
    tool("optimize_solar_storage"),
    tool("search_ny_incentives_and_rules"),
    tool("get_hazard_context"),
    *fin_steps,
]


def scenario_lines(sid, d):
    cid = d["calc_id"]
    lo, hi = d["reduction_pct_of_use"]
    glo, ghi = d["share_of_goal_pct"]
    reach = "it reaches the goal even at the low end" if d["reaches_goal"] else "it does not reach the 30% goal at the low end"
    ulo, uhi = d["upfront_usd"]
    clo, chi = d["incentives_counted_usd"]
    nlo, nhi = d["net_cost_usd"]
    plo, phi = d["payback_years"]
    slo, shi = d["annual_savings_usd"]
    olo, ohi = d["outage_hours"]
    tail = "" if ohi > 0 else " No battery, so solar shuts off in an outage."
    lines = [
        c(f"Scenario {sid} ({d['scenario_name']}) cuts grid use {lo}-{hi} % of annual use = {n(glo)}-{n(ghi)} % of the 30% goal; {reach}.", "ESTIMATE", "low", calc_id=cid, **rng(lo, hi, "% of annual use")),
        c(f"Scenario {sid} upfront cost {n(ulo)}-{n(uhi)} USD; federal credit counted {n(clo)}-{n(chi)} USD; net cost {n(nlo)}-{n(nhi)} USD; budget strain: {d['budget_strain']}.", "ESTIMATE", "low", calc_id=cid, **rng(nlo, nhi, "USD")),
        c(f"Scenario {sid} simple payback {plo}-{phi} years on savings of {n(slo)}-{n(shi)} USD/yr. Simple payback, not the full SAM model.", "ESTIMATE", "low", calc_id=cid, **rng(plo, phi, "years")),
        c(f"Scenario {sid} outage backup {olo}-{ohi} hours for critical loads.{tail}", "ESTIMATE", "low", calc_id=cid, **rng(olo, ohi, "hours")),
    ]
    return lines


gap_lo, gap_hi = C["budget_gap_usd"]
solar_lo, solar_hi = B["solar_alone_pct_of_use"]
pv = solar["source_url"]
PLUTO = rec["source_url"]
FOOT = rec["data"]["footprints_source_url"]
IRS = "https://www.irs.gov/credits-deductions/elective-pay-and-transferability"
DCAS = "https://www.nyc.gov/site/dcas/news/010-26/nycps-dcas-complete-130-solar-installations-city-school-roofs-latest-completion-marie"
NYSERDA = "https://www.nyserda.ny.gov/All-Programs/NY-Sun/Contractors/Dashboards-and-incentives/ConEd-Dashboard"
DOB = "https://www.nyc.gov/site/buildings/dob/pr-sustainable-roof-requirements.page"
EIA = rates["source_url"]
FEMA = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer"

sections = {
    "1": [
        c(f"Efficiency plus a solar array sized to the budget (Scenario B) is estimated to cut grid use by {B['reduction_pct_of_use'][0]}-{B['reduction_pct_of_use'][1]}%, which reaches the 30% goal even at the low end. Estimated cost is {n(B['upfront_usd'][0])}-{n(B['upfront_usd'][1])} USD before the federal credit, within your 800,000 USD budget.", "ESTIMATE", "low", calc_id="F-B", **rng(B["reduction_pct_of_use"][0], B["reduction_pct_of_use"][1], "% of annual use")),
        c(f"Rooftop solar alone could produce about {solar_lo}-{solar_hi}% of annual use, so it cannot reach the 30% goal by itself; efficiency has to come first.", "ESTIMATE", "medium", calc_id="F-B", **rng(solar_lo, solar_hi, "% of annual use")),
        c(f"Scenario C adds a 960 kWh backup battery and reaches the goal too, but it costs {n(gap_lo)}-{n(gap_hi)} USD more than your budget. Whether to extend the budget for backup power is your decision once you compare that gap with the savings.", "RECOMMENDATION", "medium", calc_id="F-C"),
        c(f"Capital budget USD {n(intake['budget_amount'])} ({intake['budget_year']}) from intake.", "FACT", "high", source_url=PROFILE, **rng(intake["budget_amount"], intake["budget_amount"], "USD")),
    ],
    "2": [
        c(f"{n(intake['floor_area_sqft'])} sq ft elementary school built in {intake['year_built']}, flat roof of {n(roof)} sq ft, in the Bronx, on Con Edison. These are the figures you entered.", "FACT", "high", source_url=PROFILE, **rng(intake["floor_area_sqft"], intake["floor_area_sqft"], "sq ft")),
        c("The city record for the lot (PLUTO) lists the Department of Education as owner, four floors, 46,700 sq ft of floor area, built 1994, and no landmark or historic district. Its floor area is within 7% of the 43,760 sq ft you entered.", "FACT", "high", source_url=PLUTO, **rng(46700, 46700, "sq ft")),
        c(f"NYC building footprints show one building outline on the lot of about {n(rec['data']['footprint_total_sqft'])} sq ft, which matches the roof area you entered. A footprint is ground area, not a measured roof; have an engineer or roofer confirm it.", "FACT", "medium", source_url=FOOT, **rng(rec["data"]["footprint_total_sqft"], rec["data"]["footprint_total_sqft"], "sq ft")),
        c("FEMA's current flood map puts the site in zone X, an area of minimal flood hazard, so no flood-zone review is triggered.", "FACT", "medium", source_url=FEMA),
    ],
    "3": [
        c(sd["range_assumption"], "ASSUMPTION", "medium", assumption_id="A1"),
        c("Usable roof setback factor 0.55 for edges, equipment and access paths (C1).", "ASSUMPTION", "medium", assumption_id="A2"),
        c("About 66 sq ft of roof per kW for a flat commercial array (C2).", "ASSUMPTION", "medium", assumption_id="A3"),
        c(f"Battery sizing for Scenario C is a saved sample of {battery['battery_kwh']} kWh and {battery['battery_kw']} kW, not a design for this building.", "ASSUMPTION", "low", assumption_id="A4"),
        c("Efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.", "ASSUMPTION", "low", assumption_id="A7", **rng(10, 20, "% of annual use")),
        c(B["assumption_text"], "ASSUMPTION", "low", assumption_id="A9"),
    ],
    "4": [
        c(f"Baseline is {n(use)} kWh a year of grid electricity from your entry, which matches the city's benchmarking range for this building. The 30% goal is measured against what the building buys from the grid.", "FACT", "high", source_url=PROFILE, **rng(use, use, "kWh/yr")),
        c("Start with LED lighting and controls; savings use benchmark percentages until a building model exists. You listed no efficiency work already done, so these measures are treated as open.", "RECOMMENDATION", "low", source_url=PROFILE),
        c("The plan covers grid electricity only. If the building also burns gas or oil for heat, those fuels are outside this goal.", "RECOMMENDATION", "low", source_url=PROFILE),
    ],
    "5": [
        c(f"C1 usable roof about {n(c1['value'])} sq ft ({n(roof)} x 0.55).", "ESTIMATE", "medium", calc_id="C1", **rng(c1["value"], c1["value"], "sq ft")),
        c(f"C2 array about {kw:g} kW DC ({n(c1['value'])} / 66 sq ft per kW).", "ESTIMATE", "medium", calc_id="C2", **rng(round(c2["value"], 1), round(c2["value"], 1), "kW DC")),
        c(f"PVWatts output for that array is {n(sd['annual_ac_kwh_low'])}-{n(sd['annual_ac_kwh_high'])} kWh a year, located at the school (central {n(sd['annual_ac_kwh'])} kWh).", "ESTIMATE", "medium", source_url=pv, **rng(round(sd["annual_ac_kwh_low"]), round(sd["annual_ac_kwh_high"]), "kWh/yr")),
        c(f"C3 solar offset is about {round(c3['value'] * 100, 1)}% of annual use at the central output.", "ESTIMATE", "medium", calc_id="C3", **rng(round(c3["value"] * 100, 1), round(c3["value"] * 100, 1), "% of annual use")),
        c(f"C4 annual bill savings from solar are about {n(c4_low['value'])}-{n(c4_high['value'])} USD at the New York commercial average price of {p_low}-{p_high} USD/kWh, not this building's own tariff.", "ESTIMATE", "medium", calc_id="C4", **rng(round(c4_low["value"]), round(c4_high["value"]), "USD/yr")),
    ],
    "6": [
        *scenario_lines("A", A), *scenario_lines("B", B), *scenario_lines("C", C),
        c(f"Scenario C reaches the goal, but its estimated cost is {n(gap_lo)}-{n(gap_hi)} USD more than your budget. Reaching the goal with backup power may take more than the amount set aside; compare that gap with the savings before deciding whether to extend it.", "ESTIMATE", "low", calc_id="F-C", **rng(gap_lo, gap_hi, "USD")),
        c(f"Rooftop solar alone covers only {solar_lo}-{solar_hi}% of annual use and does not reach the 30% goal.", "ESTIMATE", "medium", calc_id="F-B", **rng(solar_lo, solar_hi, "% of annual use")),
    ],
    "7": [
        c("Federal elective pay lets a governmental entity receive the solar investment credit as a direct payment. The IRS page (last updated 2026-06-27) says tax-exempt and governmental entities can use it. For solar projects that begin construction after 2026-07-04, the statute ends the credit for property placed in service after 2027-12-31, so a 2027 project must be finished and in service by then.", "FACT", "medium", source_url=IRS),
        c(f"The financial model counts a 30% federal credit on the solar and battery only: {n(B['incentives_counted_usd'][0])}-{n(B['incentives_counted_usd'][1])} USD in Scenario B. This assumes the 2027-12-31 deadline is met and the project qualifies; confirm both with a tax advisor before relying on it.", "ESTIMATE", "low", calc_id="F-B", **rng(B["incentives_counted_usd"][0], B["incentives_counted_usd"][1], "USD")),
        c("The city's Solar Schools program (DCAS, NYPA and NYC Public Schools) puts solar on DOE school roofs under power purchase agreements: 130 installations are done and 86 more are in progress (April 2026). It is uncertain whether this building is in the pipeline, so it is not counted in net cost; ask DCAS and NYC Public Schools before buying solar yourself, because if the building is in the pipeline the solar may not come out of this budget.", "RECOMMENDATION", "medium", source_url=DCAS),
        c("The NYSERDA NY-Sun commercial solar incentive is uncertain: its current block status could not be confirmed from an official page on 2026-10-16, so it is left out of net cost until checked on NYSERDA's Con Edison dashboard.", "FACT", "low", source_url=NYSERDA),
        c("Costs use benchmark prices (A9). The tariff is a saved sample (SC-9 Rate I) and the price used is the New York average from the US Energy Information Administration; confirm the tariff against a recent Con Edison bill.", "ASSUMPTION", "low", assumption_id="A9"),
    ],
    "8": [
        c("Phase 0, confirm data and budget: send 12 months of Con Edison bills, confirm the tariff against a bill, and confirm the 2027 capital budget and whether it can be extended.", "RECOMMENDATION", "high", source_url=PROFILE),
        c("Phase 1, professional reviews: structural PE/RA analysis, a roof condition survey (the roof replacement year is blank), and the roof area, before any solar design.", "RECOMMENDATION", "high", source_url=PROFILE),
        c("Phase 2, efficiency measures: LED lighting and controls first (Scenario A), the cheapest and fastest payback.", "RECOMMENDATION", "medium", calc_id="F-A"),
        c("Phase 3, permits and interconnection: licensed electrician, FDNY rooftop access review and the Con Edison interconnection application; ask DCAS and NYC Public Schools about the Solar Schools pipeline in parallel.", "RECOMMENDATION", "high", source_url=DCAS),
        c("Phase 4, solar installation: the roof array sized in Scenario B once reviews pass, and in service by 2027-12-31 to keep the federal credit.", "RECOMMENDATION", "medium", calc_id="F-B"),
        c("Phase 5, battery, commissioning and verification: add storage if the budget is extended (Scenario C) and check results against 12 months of bills.", "RECOMMENDATION", "medium", calc_id="F-C"),
    ],
    "9": [
        c(f"Scenario C's battery of {n(battery['battery_kwh'])} kWh supports about {C['outage_hours'][0]}-{C['outage_hours'][1]} hours of the {battery['critical_load_kw']} kW critical load (emergency lighting and communications).", "ESTIMATE", "low", calc_id="F-C", **rng(C["outage_hours"][0], C["outage_hours"][1], "hours")),
        c("Scenarios A and B give no backup power: solar panels shut off in an outage without a battery.", "RECOMMENDATION", "medium", calc_id="F-A"),
        c("The building is in FEMA flood zone X, so the battery can go at ground level or on the roof without a flood-zone design change; confirm the final siting with the PE of record.", "RECOMMENDATION", "low", source_url=FEMA),
    ],
    "10": [
        c("Licensed Professional Engineer or Registered Architect structural analysis for rooftop solar loads, as NYC DOB requires.", "RECOMMENDATION", "high", source_url=PROFILE),
        c("Roof condition survey by a qualified roofing contractor before design.", "RECOMMENDATION", "high", source_url=PROFILE),
        c("NYC licensed electrician for interconnection and service upgrades.", "RECOMMENDATION", "high", source_url=PROFILE),
        c("FDNY rooftop access review for equipment layout.", "RECOMMENDATION", "high", source_url=PROFILE),
        c("Con Edison utility interconnection review and application.", "RECOMMENDATION", "high", source_url=PROFILE),
        c("If the roof is replaced as part of this work, NYC Local Laws 92 and 94 of 2019 require the roof to carry a solar photovoltaic system, a green roof, or both over any applicable roof. Plan the re-roof and the array together.", "RECOMMENDATION", "medium", source_url=DOB),
        c("Coordinate with NYC Public Schools and DCAS, who manage DOE buildings, before procuring solar for this school.", "RECOMMENDATION", "medium", source_url=DCAS),
    ],
    "11": [
        c("Rooftop solar plus efficiency is unlikely to reach net-zero on this roof; plan off-site renewable procurement for the remainder.", "RECOMMENDATION", "low", calc_id="C3"),
    ],
    "12": [
        c("The tariff (SC-9 Rate I) and the battery sizing are saved samples, not live data. The tariff is stale and must be confirmed against a bill; the plan uses the live New York average price instead for savings.", "FACT", "medium", source_url=EIA),
        c("The roof area is the building outline from city footprints, not a measured roof, and the flat roof type was not checked on aerial imagery. Both need an engineer or roofer.", "FACT", "medium", source_url=FOOT),
        c("The roof replacement year is missing from the intake, so the roof's remaining life is unknown. Heat and winter-storm ratings were not looked up.", "FACT", "medium", source_url=PROFILE),
        c("The NY-Sun incentive could not be confirmed and is left out of net cost. The incentive and rule pages were read by hand on 2026-10-16; under the 7-day freshness rule they must be re-read before they are relied on after 2026-10-23.", "FACT", "medium", source_url=NYSERDA),
        c("Overall confidence is medium: the building, solar and flood data are live and agree with each other, while the costs are benchmark ranges and the tariff and battery are samples. We cannot guarantee savings; every figure is an estimate with a range.", "RECOMMENDATION", "medium", source_url=PROFILE),
    ],
    "13": [
        c("Session intake; NYC PLUTO building record; NYC building footprints; PVWatts v8; EIA electricity prices; FEMA flood map; IRS elective pay page; NYC DCAS Solar Schools release; NYC DOB sustainable roof release; NYSERDA NY-Sun dashboard; and the internal calculation and financial model tools.", "FACT", "medium", source_url=PLUTO),
    ],
}
titles = {
    "1": "Summary and goal status", "2": "Building profile and data provenance", "3": "Assumptions register",
    "4": "Baseline and efficiency opportunities", "5": "Solar assessment with calculations", "6": "Scenario comparison table",
    "7": "Cost, financing and incentives", "8": "Priority roadmap", "9": "Resilience and reliability plan",
    "10": "Required professional reviews and permits", "11": "Path to net-zero and learning resources",
    "12": "Gaps, conflicts and confidence summary", "13": "Sources",
}
final = {"type": "final", "name": "write_roadmap", "input": {"roadmap": {"sections": [
    {"section_id": sid, "title": title, "claims": sections.get(sid, [])} for sid, title in titles.items()
]}}}
steps.append(final)
write("scripted_llm.json", {
    "_comment": "SCRIPTED plan for the demo case: the numbers come from the real tools, but the words were written by us, not by Claude. Replace it with a recorded live run via record_case.",
    "steps": steps,
})
write("expected.json", {
    "_comment": "Demo case. Written before the run; checked by agent/evals.py.",
    "status": "done", "check4_passed": True,
    "roadmap_includes": ["more than your budget", "elective pay", "solar schools", "uncertain", "left out of net cost"],
    "flags_include": ["tariff_needs_user_confirmation"],
})
print("built", CASE)
print("B:", B["reduction_pct_of_use"], B["upfront_usd"], B["incentives_counted_usd"], B["net_cost_usd"], B["budget_strain"], B["payback_years"])
print("C:", C["reduction_pct_of_use"], C["upfront_usd"], C["budget_gap_usd"], C["outage_hours"])
