/**
 * Sample data for the /plan-mockup design page (THROWAWAY).
 *
 * Generated once from our five saved runs (the local replay endpoint, no Claude): the scenario numbers, label
 * counts, phases, referrals, gaps and flags are the real saved values. The headlines, next steps and outcome
 * labels in `copy` were written by hand around those numbers for the mockup. Nothing here is read from the
 * backend at run time, so the mockup works with no server.
 */

export type Range = [number, number];

export interface MockScenario {
  scenario_name: string;
  package: { efficiency_level: string; solar_kw_dc: number; battery_kwh: number };
  upfront_usd: Range;
  incentives_counted_usd: Range;
  net_cost_usd: Range;
  reduction_pct_of_use: Range;
  reaches_goal: boolean;
  annual_savings_usd: Range;
  payback_years: Range | null;
  budget_strain: string;
  budget_gap_usd: Range | null;
  budget_note: string;
  outage_hours: Range;
  surplus_solar_kwh: Range;
  solar_alone_pct_of_use: Range;
  solar_alone_exceeds_use: boolean;
}

export interface MockSample {
  id: string;
  label: string;
  kind: "recorded" | "scripted";
  tag: string;
  question: string;
  status: "done" | "partial";
  toolCalls: number;
  events: number;
  tools: string[];
  profile: Record<string, string | number | null>;
  scenarios: Partial<Record<"A" | "B" | "C", MockScenario>>;
  labelCounts: Record<string, number>;
  claimTotal: number;
  summary: string[];
  building: string[];
  assumptions: string[];
  baseline: string[];
  solar: string[];
  money: string[];
  phases: string[];
  resilience: string[];
  referrals: string[];
  gaps: string[];
  sources: string[];
  flags: string[];
  siteContext: Record<string, unknown>;
  copy: {
    outcome: string;
    tone: "good" | "caution" | "next-step";
    headline: string;
    subhead: string;
    recommended: "A" | "B" | "C";
    next: { title: string; body: string };
    incentives: { name: string; status: "open" | "uncertain" | "rule"; note: string }[] | null;
  };
}

export const SAMPLES: MockSample[] = [
 {
  "id": "demo_ps236_bronx",
  "label": "P.S. 236, Bronx: the good case",
  "kind": "scripted",
  "tag": "Goal reached within budget; backup power over budget (our script, real data)",
  "question": "How can our school cut grid electricity 30% by 2030 on an $800,000 capital budget?",
  "status": "done",
  "toolCalls": 16,
  "events": 85,
  "tools": [
   "get_building_profile",
   "lookup_ny_building_records",
   "calculate",
   "calculate",
   "get_solar_production",
   "get_utility_rates",
   "get_utility_tariff",
   "calculate",
   "calculate",
   "calculate",
   "optimize_solar_storage",
   "search_ny_incentives_and_rules",
   "get_hazard_context",
   "run_financial_model",
   "run_financial_model",
   "run_financial_model"
  ],
  "profile": {
   "building_name": "P.S. 236 Langston Hughes (DOE building X173)",
   "address": "1871 Walton Avenue",
   "borough": "Bronx",
   "building_type": "elementary school",
   "floor_area_sqft": 43760,
   "year_built": 1994,
   "roof_type": "flat",
   "roof_area_sqft": 10260,
   "annual_kwh": 456834,
   "budget_amount": 800000,
   "budget_year": 2027,
   "goal": "Cut grid electricity 30% by 2030",
   "existing_renewables": "none",
   "existing_efficiency": "none",
   "existing_solar_kw": null,
   "critical_loads": "emergency lighting and communications",
   "utility": "Con Edison"
  },
  "scenarios": {
   "A": {
    "scenario_name": "Efficiency only",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 0.0,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     175040.0,
     350080.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     175040.0,
     350080.0
    ],
    "reduction_pct_of_use": [
     10.0,
     20.0
    ],
    "reaches_goal": false,
    "annual_savings_usd": [
     9050.0,
     22092.0
    ],
    "payback_years": [
     7.9,
     38.7
    ],
    "budget_strain": "within budget",
    "budget_gap_usd": [
     0.0,
     0.0
    ],
    "budget_note": "The estimated cost fits within the budget.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     22.1,
     24.3
    ],
    "solar_alone_exceeds_use": false
   },
   "B": {
    "scenario_name": "Efficiency + solar within budget",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 85.5,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     431540.0,
     734830.0
    ],
    "incentives_counted_usd": [
     76950.0,
     115425.0
    ],
    "net_cost_usd": [
     354590.0,
     619405.0
    ],
    "reduction_pct_of_use": [
     32.1,
     44.3
    ],
    "reaches_goal": true,
    "annual_savings_usd": [
     29078.0,
     48956.0
    ],
    "payback_years": [
     7.2,
     21.3
    ],
    "budget_strain": "within budget",
    "budget_gap_usd": [
     0.0,
     0.0
    ],
    "budget_note": "The estimated cost fits within the budget.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     22.1,
     24.3
    ],
    "solar_alone_exceeds_use": false
   },
   "C": {
    "scenario_name": "Full path to the goal (deep efficiency + full solar + backup battery)",
    "package": {
     "efficiency_level": "deep",
     "solar_kw_dc": 85.5,
     "battery_kwh": 960.0
    },
    "upfront_usd": [
     1270100.0,
     2044910.0
    ],
    "incentives_counted_usd": [
     249750.0,
     403425.0
    ],
    "net_cost_usd": [
     1020350.0,
     1641485.0
    ],
    "reduction_pct_of_use": [
     37.1,
     49.3
    ],
    "reaches_goal": true,
    "annual_savings_usd": [
     33603.0,
     54479.0
    ],
    "payback_years": [
     18.7,
     48.8
    ],
    "budget_strain": "over budget",
    "budget_gap_usd": [
     470100.0,
     1244910.0
    ],
    "budget_note": "Reaches the goal, but the estimated cost is $470,100-$1,244,910 more than your budget. Reaching the goal may take more than the amount set aside; compare that gap with the savings before deciding whether to extend it.",
    "outage_hours": [
     6.8,
     8.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     22.1,
     24.3
    ],
    "solar_alone_exceeds_use": false
   }
  },
  "labelCounts": {
   "ESTIMATE": 23,
   "RECOMMENDATION": 21,
   "FACT": 13,
   "ASSUMPTION": 7
  },
  "claimTotal": 64,
  "summary": [
   "Efficiency plus a solar array sized to the budget (Scenario B) is estimated to cut grid use by 32.1-44.3%, which reaches the 30% goal even at the low end. Estimated cost is 431,540-734,830 USD before the federal credit, within your 800,000 USD budget.",
   "Rooftop solar alone could produce about 22.1-24.3% of annual use, so it cannot reach the 30% goal by itself; efficiency has to come first.",
   "Scenario C adds a 960 kWh backup battery and reaches the goal too, but it costs 470,100-1,244,910 USD more than your budget. Whether to extend the budget for backup power is your decision once you compare that gap with the savings.",
   "Capital budget USD 800,000 (2027) from intake."
  ],
  "building": [
   "43,760 sq ft elementary school built in 1994, flat roof of 10,260 sq ft, in the Bronx, on Con Edison. These are the figures you entered.",
   "The city record for the lot (PLUTO) lists the Department of Education as owner, four floors, 46,700 sq ft of floor area, built 1994, and no landmark or historic district. Its floor area is within 7% of the 43,760 sq ft you entered.",
   "NYC building footprints show one building outline on the lot of about 10,255 sq ft, which matches the roof area you entered. A footprint is ground area, not a measured roof; have an engineer or roofer confirm it.",
   "FEMA's current flood map puts the site in zone X, an area of minimal flood hazard, so no flood-zone review is triggered."
  ],
  "assumptions": [
   "ASSUMPTION: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.",
   "Usable roof setback factor 0.55 for edges, equipment and access paths (C1).",
   "About 66 sq ft of roof per kW for a flat commercial array (C2).",
   "Battery sizing for Scenario C is a saved sample of 960 kWh and 120 kW, not a design for this building.",
   "Efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.",
   "Planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open."
  ],
  "baseline": [
   "Baseline is 456,834 kWh a year of grid electricity from your entry, which matches the city's benchmarking range for this building. The 30% goal is measured against what the building buys from the grid.",
   "Start with LED lighting and controls; savings use benchmark percentages until a building model exists. You listed no efficiency work already done, so these measures are treated as open.",
   "The plan covers grid electricity only. If the building also burns gas or oil for heat, those fuels are outside this goal."
  ],
  "solar": [
   "C1 usable roof about 5,643 sq ft (10,260 x 0.55).",
   "C2 array about 85.5 kW DC (5,643 / 66 sq ft per kW).",
   "PVWatts output for that array is 101,100-111,098 kWh a year, located at the school (central 106,101 kWh).",
   "C3 solar offset is about 23.2% of annual use at the central output.",
   "C4 annual bill savings from solar are about 20,028-26,864 USD at the New York commercial average price of 0.1981-0.2418 USD/kWh, not this building's own tariff."
  ],
  "money": [
   "Federal elective pay lets a governmental entity receive the solar investment credit as a direct payment. The IRS page (last updated 2026-06-27) says tax-exempt and governmental entities can use it. For solar projects that begin construction after 2026-07-04, the statute ends the credit for property placed in service after 2027-12-31, so a 2027 project must be finished and in service by then.",
   "The financial model counts a 30% federal credit on the solar and battery only: 76,950-115,425 USD in Scenario B. This assumes the 2027-12-31 deadline is met and the project qualifies; confirm both with a tax advisor before relying on it.",
   "The city's Solar Schools program (DCAS, NYPA and NYC Public Schools) puts solar on DOE school roofs under power purchase agreements: 130 installations are done and 86 more are in progress (April 2026). It is uncertain whether this building is in the pipeline, so it is not counted in net cost; ask DCAS and NYC Public Schools before buying solar yourself, because if the building is in the pipeline the solar may not come out of this budget.",
   "The NYSERDA NY-Sun commercial solar incentive is uncertain: its current block status could not be confirmed from an official page on 2026-10-16, so it is left out of net cost until checked on NYSERDA's Con Edison dashboard.",
   "Costs use benchmark prices (A9). The tariff is a saved sample (SC-9 Rate I) and the price used is the New York average from the US Energy Information Administration; confirm the tariff against a recent Con Edison bill."
  ],
  "phases": [
   "Phase 0, confirm data and budget: send 12 months of Con Edison bills, confirm the tariff against a bill, and confirm the 2027 capital budget and whether it can be extended.",
   "Phase 1, professional reviews: structural PE/RA analysis, a roof condition survey (the roof replacement year is blank), and the roof area, before any solar design.",
   "Phase 2, efficiency measures: LED lighting and controls first (Scenario A), the cheapest and fastest payback.",
   "Phase 3, permits and interconnection: licensed electrician, FDNY rooftop access review and the Con Edison interconnection application; ask DCAS and NYC Public Schools about the Solar Schools pipeline in parallel.",
   "Phase 4, solar installation: the roof array sized in Scenario B once reviews pass, and in service by 2027-12-31 to keep the federal credit.",
   "Phase 5, battery, commissioning and verification: add storage if the budget is extended (Scenario C) and check results against 12 months of bills."
  ],
  "resilience": [
   "Scenario C's battery of 960 kWh supports about 6.8-8.0 hours of the 120 kW critical load (emergency lighting and communications).",
   "Scenarios A and B give no backup power: solar panels shut off in an outage without a battery.",
   "The building is in FEMA flood zone X, so the battery can go at ground level or on the roof without a flood-zone design change; confirm the final siting with the PE of record."
  ],
  "referrals": [
   "Licensed Professional Engineer or Registered Architect structural analysis for rooftop solar loads, as NYC DOB requires.",
   "Roof condition survey by a qualified roofing contractor before design.",
   "NYC licensed electrician for interconnection and service upgrades.",
   "FDNY rooftop access review for equipment layout.",
   "Con Edison utility interconnection review and application.",
   "If the roof is replaced as part of this work, NYC Local Laws 92 and 94 of 2019 require the roof to carry a solar photovoltaic system, a green roof, or both over any applicable roof. Plan the re-roof and the array together.",
   "Coordinate with NYC Public Schools and DCAS, who manage DOE buildings, before procuring solar for this school."
  ],
  "gaps": [
   "The tariff (SC-9 Rate I) and the battery sizing are saved samples, not live data. The tariff is stale and must be confirmed against a bill; the plan uses the live New York average price instead for savings.",
   "The roof area is the building outline from city footprints, not a measured roof, and the flat roof type was not checked on aerial imagery. Both need an engineer or roofer.",
   "The roof replacement year is missing from the intake, so the roof's remaining life is unknown. Heat and winter-storm ratings were not looked up.",
   "The NY-Sun incentive could not be confirmed and is left out of net cost. The incentive and rule pages were read by hand on 2026-10-16; under the 7-day freshness rule they must be re-read before they are relied on after 2026-10-23.",
   "Overall confidence is medium: the building, solar and flood data are live and agree with each other, while the costs are benchmark ranges and the tariff and battery are samples. We cannot guarantee savings; every figure is an estimate with a range."
  ],
  "sources": [
   "Session intake; NYC PLUTO building record; NYC building footprints; PVWatts v8; EIA electricity prices; FEMA flood map; IRS elective pay page; NYC DCAS Solar Schools release; NYC DOB sustainable roof release; NYSERDA NY-Sun dashboard; and the internal calculation and financial model tools."
  ],
  "flags": [
   "missing_field:roof_replaced_year",
   "statewide_average_rate",
   "tariff_needs_user_confirmation",
   "stale_data"
  ],
  "siteContext": {
   "roof_kind": "flat",
   "flood_zone": "X"
  },
  "copy": {
   "outcome": "Goal reached within budget",
   "tone": "good",
   "headline": "Yes. You can reach your 30% goal inside your $800,000 budget.",
   "subhead": "Plan B (LED lighting and controls plus an 85 kW roof array) is estimated to cut P.S. 236's grid electricity by 32 to 44 percent, for about $432k to $735k before the federal credit.",
   "recommended": "B",
   "next": {
    "title": "Before you buy solar, ask the city",
    "body": "NYC's Solar Schools program is putting solar on DOE roofs under power purchase agreements. If this building is in that pipeline, the panels may not come out of your budget at all. Ask DCAS and NYC Public Schools first."
   },
   "incentives": [
    {
     "name": "Federal elective pay (solar credit)",
     "status": "open",
     "note": "Government entities can receive the credit as a direct payment. Solar must be in service by Dec 31, 2027."
    },
    {
     "name": "NYC Solar Schools (DCAS, NYPA, NYC Public Schools)",
     "status": "uncertain",
     "note": "130 school roofs done, 86 more in progress. Not known whether this building is in the pipeline."
    },
    {
     "name": "NYSERDA NY-Sun commercial incentive",
     "status": "uncertain",
     "note": "Could not be confirmed from an official page, so it is left out of the cost."
    },
    {
     "name": "NYC Local Laws 92 and 94 (sustainable roofs)",
     "status": "rule",
     "note": "If the roof is replaced, it must carry solar, a green roof, or both."
    }
   ]
  }
 },
 {
  "id": "real3_ps38_staten_island",
  "label": "P.S. 38, Staten Island",
  "kind": "recorded",
  "tag": "Surplus solar not counted; backup far over budget",
  "question": "How can our school cut grid power 30% by 2030 on a $600k capital budget?",
  "status": "done",
  "toolCalls": 16,
  "events": 85,
  "tools": [
   "get_building_profile",
   "lookup_ny_building_records",
   "calculate",
   "calculate",
   "get_solar_production",
   "get_utility_rates",
   "get_utility_tariff",
   "search_ny_incentives_and_rules",
   "get_hazard_context",
   "optimize_solar_storage",
   "calculate",
   "calculate",
   "calculate",
   "run_financial_model",
   "run_financial_model",
   "run_financial_model"
  ],
  "profile": {
   "building_name": "P.S. 38 (R038)",
   "address": "421 Lincoln Avenue",
   "borough": "Staten Island",
   "building_type": "elementary school",
   "floor_area_sqft": 55860,
   "year_built": 1955,
   "roof_type": "flat",
   "roof_area_sqft": 34360,
   "annual_kwh": 284403,
   "budget_amount": 600000,
   "budget_year": 2027,
   "goal": "Cut grid electricity 30% by 2030",
   "existing_renewables": "none",
   "existing_efficiency": "none",
   "existing_solar_kw": null,
   "critical_loads": "emergency lighting and communications",
   "utility": "Con Edison"
  },
  "scenarios": {
   "A": {
    "scenario_name": "Efficiency only",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 0.0,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     223440.0,
     446880.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     223440.0,
     446880.0
    ],
    "reduction_pct_of_use": [
     10.0,
     20.0
    ],
    "reaches_goal": false,
    "annual_savings_usd": [
     5634.0,
     13754.0
    ],
    "payback_years": [
     16.2,
     79.3
    ],
    "budget_strain": "within budget",
    "budget_gap_usd": [
     0.0,
     0.0
    ],
    "budget_note": "The estimated cost fits within the budget.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     118.9,
     130.7
    ],
    "solar_alone_exceeds_use": true
   },
   "B": {
    "scenario_name": "Efficiency + solar within budget",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 34.0,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     325520.0,
     600000.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     325520.0,
     600000.0
    ],
    "reduction_pct_of_use": [
     24.1,
     35.5
    ],
    "reaches_goal": false,
    "annual_savings_usd": [
     13594.0,
     24432.0
    ],
    "payback_years": [
     13.3,
     44.1
    ],
    "budget_strain": "within budget",
    "budget_gap_usd": [
     0.0,
     0.0
    ],
    "budget_note": "The estimated cost fits within the budget.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     118.9,
     130.7
    ],
    "solar_alone_exceeds_use": true
   },
   "C": {
    "scenario_name": "Full path to the goal (deep efficiency + full solar + backup battery)",
    "package": {
     "efficiency_level": "deep",
     "solar_kw_dc": 286.3,
     "battery_kwh": 960.0
    },
    "upfront_usd": [
     1993600.0,
     3142260.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     1993600.0,
     3142260.0
    ],
    "reduction_pct_of_use": [
     100.0,
     100.0
    ],
    "reaches_goal": true,
    "annual_savings_usd": [
     56340.0,
     68769.0
    ],
    "payback_years": [
     29.0,
     55.8
    ],
    "budget_strain": "over budget",
    "budget_gap_usd": [
     1393600.0,
     2542260.0
    ],
    "budget_note": "Reaches the goal, but the estimated cost is $1,393,600-$2,542,260 more than your budget. Reaching the goal may take more than the amount set aside; compare that gap with the savings before deciding whether to extend it.",
    "outage_hours": [
     6.8,
     8.0
    ],
    "surplus_solar_kwh": [
     96405.0,
     158303.0
    ],
    "solar_alone_pct_of_use": [
     118.9,
     130.7
    ],
    "solar_alone_exceeds_use": true
   }
  },
  "labelCounts": {
   "FACT": 14,
   "ESTIMATE": 20,
   "RECOMMENDATION": 20,
   "ASSUMPTION": 16
  },
  "claimTotal": 70,
  "summary": [
   "Goal: cut grid electricity 30% by 2030 on a $600,000 capital budget (budget year 2027) at P.S. 38, 421 Lincoln Avenue, Staten Island.",
   "Scenario A (standard efficiency only) costs about $223,440-$446,880 and cuts about 10-20% of annual use. It fits the budget but does not reach the 30% goal (33-67% of the goal).",
   "Scenario B (standard efficiency plus a 34 kW solar array sized to the budget) costs about $325,520-$600,000 and cuts about 24.1-35.5% of annual use. It fits the budget. It does not reliably reach the goal because the low end is below 30%; the high end is above it.",
   "Scenario C (deep efficiency, whole-roof array of about 286 kW and a 960 kWh battery) reaches the goal, with a modeled reduction of 100% of annual use. It costs about $1,393,600-$2,542,260 more than your budget. Meeting the goal at full scale may take more than $600,000. Whether to extend the budget is your decision once you compare that gap with the savings.",
   "On the figures the tools returned, the most budget-realistic route is efficiency plus a budget-sized solar array (Scenario B). It may land near the 30% goal but is not certain to reach it. These are planning-level estimates, not quotes, and I cannot guarantee savings."
  ],
  "building": [
   "Entered by you: elementary school, 55,860 sq ft floor area, built 1955, flat roof of 34,360 sq ft, annual grid use 284,403 kWh, Con Edison, critical loads are emergency lighting and communications. Existing renewables: none. Existing efficiency work: none. So the plan assumes no existing systems and recommends no measure you already have.",
   "The baseline for the goal is the electricity the building buys from the grid: 284,403 kWh per year, from the bills you entered. There is no existing solar to lower it.",
   "The city record (PLUTO) lists gross floor area of 17,620 sq ft for this lot, which differs from the 55,860 sq ft you entered. The lot area is 65,000 sq ft, so the lot size does not match your floor area. I kept your 55,860 sq ft as the working figure. Please confirm it. Efficiency cost benchmarks scale with floor area, so efficiency costs would be lower if the city figure were correct.",
   "City building footprints show 3 buildings on the lot totaling 34,363 sq ft of ground area, which is close to the 34,360 sq ft roof area you entered. A footprint is ground area, not a measured roof, and it may include buildings you do not intend to use. The roof area is your number, so have an engineer or roofer verify it.",
   "Neither the profile nor the city record marks the building as a landmark. The record lists no parkland flag."
  ],
  "assumptions": [
   "ASSUMPTION A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.",
   "ASSUMPTION A2: usable roof setback factor 0.55 (C1).",
   "ASSUMPTION A3: array density of 66 sq ft per kW DC (C2).",
   "ASSUMPTION A4: sample battery size (fictional REopt stand-in sized for 8 hours of backup), not a site-specific design.",
   "ASSUMPTION A5: incentive programs and rules come from a mock sample fixture and are pending live verification.",
   "ASSUMPTION A6: hazard ratings come from a mock sample fixture and are pending site-specific assessment.",
   "ASSUMPTION A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.",
   "ASSUMPTION A9: planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%. The 30% federal credit counts only when the incentives tool says the program is open."
  ],
  "baseline": [
   "Baseline grid use is 284,403 kWh per year. The bills are in the intake, so no benchmark use was needed.",
   "Standard efficiency (for example LED lighting and controls) is estimated to cut 28,440-56,881 kWh per year, which is 10-20% of use, at a cost of about $223,440-$446,880. Because the building has no efficiency work done, no benchmark savings are reduced for existing work. There is no building model, so confidence is low.",
   "Efficiency savings of 10-20% of annual use are a published benchmark, not a model of this school.",
   "Get an investment-grade energy audit to replace the benchmark with measured savings, and check the 55,860 sq ft floor area first. The cost benchmarks depend on it."
  ],
  "solar": [
   "Usable roof area is about 18,898 sq ft (34,360 sq ft times the 0.55 setback factor).",
   "Array size that fits the usable roof is about 286 kW DC (at 66 sq ft per kW).",
   "PVWatts estimates the whole-roof array produces about 338,147-371,605 kWh per year (central about 354,876 kWh). The model used a 10-degree tilt facing south on a flat roof.",
   "The solar range comes from the loss band: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.",
   "The gross value of the whole-roof production at the EIA statewide commercial price is about $66,987-$89,854 per year (central about $78,783). This values all production, including surplus. The scenario savings in section 6 credit only the solar that replaces power the building still uses.",
   "The roof could produce more than the building uses: whole-roof solar alone is about 118.9-130.7% of annual use. The surplus is potential that flows to the grid. It is not counted in the savings because export credits depend on net-metering rules that were not checked.",
   "Electricity price: the EIA New York commercial 12-month average is about $0.2220 per kWh (range $0.1981-$0.2418) as of July 2026. This is a statewide average, not this building's own tariff.",
   "Have an engineer or roofer verify the roof area, the usable area after setbacks, shading and structure before any design. Roof area is your number and is not verified."
  ],
  "money": [
   "No incentive is counted in any net-cost figure. The incentive tool returned mock sample data retrieved 2025-10-01, which is stale. It lists a federal commercial ITC (placed-in-service deadline 2027-12-31) and a NY-Sun commercial incentive as open. These programs are uncertain and are left out of net cost. They may not apply to a public school, so confirm eligibility on the official program pages.",
   "Scenario A and Scenario B fit the $600,000 capital budget. Scenario C costs $1,393,600-$2,542,260 more than your budget and reaches the goal. Meeting the goal may take more than the budget. Whether to extend it is your decision once you compare that gap with the savings.",
   "Costs use planning-level benchmark prices, not quotes. Get contractor quotes before committing the 2027 capital budget.",
   "Because the incentive data is stale and mock, check the current status of the federal credit and NY-Sun on the official pages. Re-run the scenarios if a program is open to public schools. Any favorable change should be counted only after it is confirmed."
  ],
  "phases": [
   "Phase 0, confirm data and budget: confirm the floor area (55,860 vs 17,620 sq ft), roof area, 12 months of bills, budget year and type (2027 capital), the roof replacement year, and the actual Con Edison tariff.",
   "Phase 1, professional reviews: have a licensed structural PE/RA analyze the roof and complete a roof condition survey before design. I cannot certify that the roof can hold panels.",
   "Phase 2, efficiency measures: install the standard efficiency package (LED lighting and controls) first, since it lowers the load that solar must cover.",
   "Phase 3, permits and interconnection: engage a licensed electrician, obtain NYC permits, arrange FDNY rooftop access and file the Con Edison interconnection application.",
   "Phase 4, solar installation: install the budget-sized array (about 34 kW in Scenario B), leaving room to add more roof capacity later if funding allows.",
   "Phase 5, battery, commissioning and verification: add a battery if funding is extended, commission the system and compare metered results with bills against the 2030 goal."
  ],
  "resilience": [
   "Scenario C's battery would carry the critical loads (emergency lighting and communications) for about 6.8-8.0 hours in an outage.",
   "Scenarios A and B give no backup power. Solar panels shut off in an outage without a battery.",
   "ASSUMPTION A4: the battery is a sample size (960 kWh, 120 kW) from a fictional stand-in sized for 8 hours of cooling-center backup, not for this school's emergency lighting and communications. It likely oversizes the battery for those loads and should be re-sized.",
   "The hazard sample shows flood zone X, low flood rating, moderate heat and moderate winter storm. It is mock data (A6) and notes a Queens site, so it may not describe this lot. No flood-zone review is triggered by zone X, but confirm the zone against official FEMA/NYC flood maps."
  ],
  "referrals": [
   "Structural analysis by a licensed PE or RA is required before solar. I cannot certify the roof can hold the panels.",
   "A roof condition survey is required. The roof replacement year is missing from the intake, and the roof's remaining life affects the panel installation.",
   "A licensed electrician must design and install the system. FDNY rooftop access and setback review is required.",
   "A Con Edison utility interconnection review and application is required. Check net-metering and export rules before counting any surplus.",
   "Verify the roof area and the floor area with an engineer or roofer and the city record."
  ],
  "gaps": [
   "Flag intake_mismatch:floor_area_sqft: you entered 55,860 sq ft and the city record shows 17,620 sq ft gross floor area. The lot is 65,000 sq ft. I kept your value, and ask you to confirm it. Efficiency costs and savings carry low confidence until then.",
   "Flag missing_field:roof_replaced_year: the roof age is unknown, so the roof condition and remaining life are unknown. Solar confidence is lowered. Please provide it.",
   "Flag statewide_average_rate: the price is the New York commercial average, not this building's own tariff.",
   "Flags tariff_needs_user_confirmation, mock_data_in_live_run and stale_data: the tariff returned is sample data, SC-9 Rate I (General Large), effective 2025-07-01, retrieved 2025-10-01, with energy $0.20-$0.24 per kWh. It is not confirmed against a bill. Please confirm your actual tariff.",
   "Flags mock_data_in_live_run and stale_data: the incentive (A5), hazard (A6) and battery (A4) results are saved sample data retrieved 2025-10-01, so they are not facts. Confidence is low and no incentive is counted.",
   "The roof area you entered is close to the city's footprint total, but a footprint is ground area, not a measured roof. Have it verified.",
   "Net-metering and export credit rules were not checked, so the solar surplus is not credited. Payback figures are simple paybacks and not the full SAM model.",
   "I cannot guarantee savings. Every figure is an estimate with a range. I did not save any data to the reference cache, because none of it came from a verified official page."
  ],
  "sources": [
   "Your intake profile (entered by you).",
   "NYC PLUTO tax lot data, dataset pluto-26v2, retrieved 2026-10-15.",
   "PVWatts v8 solar production, retrieved 2026-10-15.",
   "EIA electricity retail price data (July 2026), retrieved 2026-10-15.",
   "Scenario results come from the planning-level financial model (F-A, F-B, F-C). Tariff, incentive, hazard and battery data are saved sample data and are not sources of fact."
  ],
  "flags": [
   "missing_field:roof_replaced_year",
   "intake_mismatch:floor_area_sqft",
   "statewide_average_rate",
   "tariff_needs_user_confirmation",
   "stale_data",
   "mock_data_in_live_run"
  ],
  "siteContext": {
   "roof_kind": "flat",
   "flood_zone": "X"
  },
  "copy": {
   "outcome": "Close, but not certain",
   "tone": "caution",
   "headline": "Close. 30% is within reach on $600,000, but not certain.",
   "subhead": "Plan B cuts grid electricity by an estimated 24 to 35 percent, so the goal is reached at the high end but not the low end. Backup power would cost about $1.4M to $2.5M more than your budget.",
   "recommended": "B",
   "next": {
    "title": "Confirm your floor and roof area first",
    "body": "The city's record for this lot says 17,620 sq ft; your form says 55,860. Every solar and cost number depends on which is right."
   },
   "incentives": null
  }
 },
 {
  "id": "real2_red_hook_rec_center",
  "label": "Red Hook Recreation Center, Brooklyn",
  "kind": "recorded",
  "tag": "Landmark on parkland, Sandy flood history, backup over budget",
  "question": "Our rec center flooded in Hurricane Sandy and is used as a cooling center. How do we cut grid power 30% by 2030 and keep critical loads running in outages, on $750k?",
  "status": "done",
  "toolCalls": 17,
  "events": 90,
  "tools": [
   "get_building_profile",
   "lookup_ny_building_records",
   "calculate",
   "calculate",
   "get_solar_production",
   "get_utility_rates",
   "get_utility_tariff",
   "search_ny_incentives_and_rules",
   "get_hazard_context",
   "optimize_solar_storage",
   "calculate",
   "calculate",
   "calculate",
   "calculate",
   "run_financial_model",
   "run_financial_model",
   "run_financial_model"
  ],
  "profile": {
   "building_name": "Red Hook Recreation Center (NYC Parks)",
   "address": "155 Bay Street",
   "borough": "Brooklyn",
   "building_type": "park recreation center",
   "floor_area_sqft": 27069,
   "year_built": 1936,
   "roof_type": "flat",
   "roof_area_sqft": 32860,
   "annual_kwh": 375066,
   "budget_amount": 750000,
   "budget_year": 2027,
   "goal": "Cut grid electricity 30% by 2030",
   "existing_renewables": null,
   "existing_efficiency": null,
   "existing_solar_kw": null,
   "critical_loads": "gym cooling, lighting and communications for a cooling center",
   "utility": "Con Edison"
  },
  "scenarios": {
   "A": {
    "scenario_name": "Efficiency only",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 0.0,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     108276.0,
     216552.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     108276.0,
     216552.0
    ],
    "reduction_pct_of_use": [
     10.0,
     20.0
    ],
    "reaches_goal": false,
    "annual_savings_usd": [
     7430.0,
     18138.0
    ],
    "payback_years": [
     6.0,
     29.1
    ],
    "budget_strain": "within budget",
    "budget_gap_usd": [
     0.0,
     0.0
    ],
    "budget_note": "The estimated cost fits within the budget.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     87.4,
     96.0
    ],
    "solar_alone_exceeds_use": false
   },
   "B": {
    "scenario_name": "Efficiency + solar within budget",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 118.5,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     463908.0,
     750000.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     463908.0,
     750000.0
    ],
    "reduction_pct_of_use": [
     47.8,
     61.6
    ],
    "reaches_goal": true,
    "annual_savings_usd": [
     35544.0,
     55842.0
    ],
    "payback_years": [
     8.3,
     21.1
    ],
    "budget_strain": "within budget",
    "budget_gap_usd": [
     0.0,
     0.0
    ],
    "budget_note": "The estimated cost fits within the budget.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     87.4,
     96.0
    ],
    "solar_alone_exceeds_use": false
   },
   "C": {
    "scenario_name": "Full path to the goal (deep efficiency + full solar + backup battery)",
    "package": {
     "efficiency_level": "deep",
     "solar_kw_dc": 273.8,
     "battery_kwh": 960.0
    },
    "upfront_usd": [
     1668190.0,
     2625354.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     1668190.0,
     2625354.0
    ],
    "reduction_pct_of_use": [
     100.0,
     100.0
    ],
    "reaches_goal": true,
    "annual_savings_usd": [
     74301.0,
     90691.0
    ],
    "payback_years": [
     18.4,
     35.3
    ],
    "budget_strain": "over budget",
    "budget_gap_usd": [
     918190.0,
     1875354.0
    ],
    "budget_note": "Reaches the goal, but the estimated cost is $918,190-$1,875,354 more than your budget. Reaching the goal may take more than the amount set aside; compare that gap with the savings before deciding whether to extend it.",
    "outage_hours": [
     6.8,
     8.0
    ],
    "surplus_solar_kwh": [
     9015.0,
     78889.0
    ],
    "solar_alone_pct_of_use": [
     87.4,
     96.0
    ],
    "solar_alone_exceeds_use": false
   }
  },
  "labelCounts": {
   "ESTIMATE": 23,
   "RECOMMENDATION": 20,
   "ASSUMPTION": 17,
   "FACT": 14
  },
  "claimTotal": 74,
  "summary": [
   "Scenario B (standard efficiency plus a 118.5 kW solar array) is estimated to cut grid purchases by about 47.8-61.6% of annual use, above the 30% goal. Its estimated cost is $463,908-$750,000, which fits the $750,000 budget (the high end uses all of it). It gives no backup power in an outage.",
   "Scenario A (efficiency only) is estimated to cut 10-20% of annual use. It does not reach the 30% goal on its own. It costs $108,276-$216,552.",
   "Scenario C (deep efficiency, whole-roof solar and a 960 kWh battery) reaches the goal and gives 6.8-8.0 hours of critical-load backup. It costs $1,668,190-$2,625,354. That is $918,190-$1,875,354 more than your $750,000 budget.",
   "Meeting both the 30% goal and outage backup for the cooling center may take more than $750,000. Whether to extend the budget is your decision, after you compare the gap with the savings. I can't guarantee savings. Every figure here is an estimate range based on planning-level benchmark prices.",
   "Planning-level benchmark prices, not quotes, sit behind all three scenarios."
  ],
  "building": [
   "You entered: Red Hook Recreation Center (NYC Parks), 155 Bay Street, Brooklyn; built 1936; flat roof; 27,069 sq ft floor area; 32,860 sq ft roof area; Con Edison customer; 2027 capital budget of $750,000.",
   "The baseline for the goal is the electricity the building buys from the grid: 375,066 kWh per year, from the intake.",
   "The city record (PLUTO) lists 21,600 sq ft gross floor area, but you entered 27,069 sq ft. I kept your 27,069 sq ft as the working figure. Please confirm which is right. The lot is 212,400 sq ft, which does not match your floor area.",
   "The city's address for this lot is 140 Lorraine Street, while you gave 155 Bay Street. It may be another frontage of the same lot. The geocoder matched 155 Bay Street to this lot (tax lot 3005820001).",
   "City building footprints show 4 buildings on the lot totaling 32,862 sq ft (27,000; 4,370; 825; 667). That is close to your 32,860 sq ft roof area, but a footprint is ground area, not a measured roof, and the lot holds more than one building. I used your roof area; please confirm it with an engineer or roofer.",
   "The city record flags this site as a landmark, and the site is NYC Parks parkland.",
   "You did not list existing solar, other renewables or efficiency work already done. The plan assumes there are none. Please tell me if any exist already (for example LED lighting), because that would lower the savings and the roof area available."
  ],
  "assumptions": [
   "A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.",
   "A2: usable roof setback factor 0.55 (C1).",
   "A3: array density factor 66 sq ft per kW DC (C2).",
   "A4: battery sizing comes from a fictional REopt stand-in sized for 8 hours of cooling-center backup (saved sample data).",
   "A5: incentive programs and rules come from a mock sample fixture, pending live verification.",
   "A6: hazard ratings come from a mock sample fixture, pending a site-specific assessment.",
   "A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.",
   "A9: planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open."
  ],
  "baseline": [
   "Grid electricity bought today is 375,066 kWh per year. The 30% goal is about 112,520 kWh per year.",
   "A standard efficiency package (LED and controls) is estimated to save 37,507-75,013 kWh per year (10-20% of use). It costs $108,276-$216,552 and saves about $7,430-$18,138 per year. This is a benchmark, not a building model.",
   "The efficiency savings benchmark is 10-20% of annual use. I did not use a building model.",
   "Start with LED lighting and controls, then have an energy auditor review cooling for the gym, which is a critical load. Efficiency work already done would lower these savings. I assumed none."
  ],
  "solar": [
   "Usable roof for solar is about 18,073 sq ft, from your 32,860 sq ft roof with a 0.55 setback factor.",
   "The whole usable roof fits an array of about 273.8 kW DC, at 66 sq ft per kW.",
   "Annual solar output for that array is estimated at 327,822-360,189 kWh (central 344,031 kWh). The range comes from the loss band in A1. PVWatts assumed a flat roof at 10 degree tilt facing south.",
   "The central output is about 0.92 of annual use.",
   "Whole-roof solar alone is modeled at about 87-96% of annual use. That is far above the 15-25% typical for rooftop solar, because this roof is large compared with 375,066 kWh of use. Please confirm the roof area and structure before relying on it. Solar alone also gives no backup power in an outage.",
   "Gross solar savings are estimated at $64,941-$87,094 per year (central $76,375). They use the EIA New York commercial average price of $0.1981-$0.2418 per kWh (central $0.222), not this building's own tariff.",
   "Under Scenario C the roof could make 9,015-78,889 kWh per year more than the building uses. That surplus is not counted in the savings, because export credits depend on net-metering rules I did not check."
  ],
  "money": [
   "Net cost equals upfront cost in every scenario because no incentive is counted: A $108,276-$216,552; B $463,908-$750,000; C $1,668,190-$2,625,354.",
   "Left out of net cost: the Federal commercial ITC (sample data lists it as open with a 2027-12-31 placed-in-service deadline) and a NYSERDA NY-Sun commercial incentive. Both come from saved sample data retrieved 2025-10-01, so they are stale and uncertain. They are not counted until checked on the official pages.",
   "The budget is a 2027 capital budget of $750,000. Scenario B fits it, but B has no battery. Scenario C adds backup but costs $918,190-$1,875,354 more than your budget. Whether to extend the budget is your decision.",
   "Ask for contractor quotes for B and for a middle option that adds a smaller battery to B. I have not costed that option. Also ask NYC Parks capital staff whether other city, state or federal funds are open. I confirmed none from official pages."
  ],
  "phases": [
   "Phase 0, confirm data and budget: collect 12 months of Con Edison bills, confirm the 2027 capital budget, confirm the tariff (sample shows SC-9 Rate I, effective 2025-07-01), and confirm floor area, roof area and any existing systems.",
   "Phase 1, professional reviews: a structural PE/RA analysis of the roof and a roof condition survey (the roof replacement year is unknown). Also have an engineer or roofer verify the usable roof area. I cannot certify that the roof can hold the panels.",
   "Phase 2, efficiency measures: LED lighting, controls and a cooling review, estimated to save 10-20% of annual use.",
   "Phase 3, permits and interconnection: Con Edison interconnection application, a licensed electrician, FDNY rooftop access review, and the LPC advisory report and parkland review in section 10.",
   "Phase 4, solar installation: start with the budget-capped 118.5 kW array (Scenario B), or the whole roof if the budget is extended, after the structural review.",
   "Phase 5, battery, commissioning and verification: add a battery with a critical-load panel, placed above flood level. Commission, then check results against 12 months of bills."
  ],
  "resilience": [
   "Scenario C's battery (960 kWh, 120 kW) is estimated to carry critical loads for 6.8-8.0 hours. The battery size is sample data.",
   "Battery sizing is a fictional REopt stand-in sized for 8 hours of cooling-center backup.",
   "Scenarios A and B give no backup power (0 hours). Solar panels shut off in an outage without a battery.",
   "Critical loads: gym cooling, lighting and communications for the cooling center.",
   "You say the center flooded in Hurricane Sandy. The sample hazard data shows flood zone X and low flood rating, but it is marked for a Queens site and is stale, so I did not rely on it. Put the battery, inverters and switchgear on the roof or above the design flood elevation.",
   "Confirm with NYC Parks how many hours or days of cooling-center operation are required. About 8 hours may not cover a multi-day outage, and longer backup would cost more."
  ],
  "referrals": [
   "A licensed PE or RA must do the structural analysis. A roof condition survey is also required. I cannot certify the roof.",
   "A licensed electrician, FDNY rooftop access review and a Con Edison interconnection review are required.",
   "The site is flagged as a landmark and is on parkland. The Landmarks Preservation Commission gives the owning agency an advisory report, not a permit, so request that review before rooftop or exterior work.",
   "Counsel should do a parkland use review before any solar or battery work.",
   "Do a flood-zone review (NYC Building Code Appendix G) against the official flood maps. The center flooded in Sandy, and the sample data that says zone X is unreliable."
  ],
  "gaps": [
   "Missing from the intake: the roof replacement year and existing systems. The plan assumes no existing solar or efficiency work. Please confirm.",
   "Floor area conflict: you entered 27,069 sq ft and the city record shows 21,600 sq ft. I used 27,069. The efficiency cost and savings depend on it, so confidence is lowered. The city address (140 Lorraine Street) also differs from yours (155 Bay Street).",
   "Electricity price is the New York commercial statewide average, not this building's tariff. It covers the 12 months to 2026-07.",
   "Tariff: the sample shows Con Edison SC-9 Rate I (General Large), effective 2025-07-01. It is mock data retrieved 2025-10-01 and stale (over a year old; the limit is 90 days). Please confirm the tariff against a bill.",
   "Incentive data is saved sample data from 2025-10-01, past the 7-day limit. It was not refreshed or saved to the cache, and is left out of net cost.",
   "Hazard data is saved sample data from 2025-10-01, labeled for a Queens site. It shows flood zone X, which conflicts with your Sandy flooding. I kept the cautious flood plan.",
   "Battery sizing and outage hours come from sample data and are low confidence.",
   "The modeled solar share of use (87-96%) is far above typical, and the roof area may span four buildings. Confidence in solar-based results is medium to low until an engineer verifies the roof area."
  ],
  "sources": [
   "NYC PLUTO tax lot data (building records and footprints), retrieved 2026-10-15.",
   "PVWatts v8 solar production, retrieved 2026-10-15.",
   "EIA electricity retail price data, retrieved 2026-10-15.",
   "Intake profile entered by you.",
   "Sample (mock) data for incentives, hazard and battery sizing: not official sources."
  ],
  "flags": [
   "missing_field:roof_replaced_year",
   "missing_field:existing_systems",
   "intake_mismatch:floor_area_sqft",
   "address_street_mismatch",
   "statewide_average_rate",
   "tariff_needs_user_confirmation",
   "stale_data",
   "mock_data_in_live_run"
  ],
  "siteContext": {
   "parkland": true,
   "roof_kind": "flat",
   "landmark": true,
   "flood_zone": "X"
  },
  "copy": {
   "outcome": "Goal yes, backup power over budget",
   "tone": "caution",
   "headline": "Yes for the goal. Backup power is the part that costs more.",
   "subhead": "Plan B is estimated to cut grid electricity by 48 to 62 percent within your $750,000, but it gives no backup power. Keeping the cooling center running adds roughly $0.9M to $1.9M beyond the budget.",
   "recommended": "B",
   "next": {
    "title": "Three reviews come before any solar",
    "body": "This is a landmark on city parkland that flooded in Hurricane Sandy. Plan for a Landmarks Preservation Commission advisory review, a parkland review by counsel, and flood protection for the battery and electrical equipment."
   },
   "incentives": null
  }
 },
 {
  "id": "real1_jefferson_market_library",
  "label": "Jefferson Market Library, Manhattan",
  "kind": "recorded",
  "tag": "Pitched roof: needs an engineer or roofer before solar is sized",
  "question": "Our library is in the Greenwich Village Historic District. Can we put solar on the roof, and how do we cut grid power 30% by 2030 on $500k?",
  "status": "partial",
  "toolCalls": 8,
  "events": 43,
  "tools": [
   "get_building_profile",
   "lookup_ny_building_records",
   "get_hazard_context",
   "get_utility_rates",
   "get_utility_tariff",
   "search_ny_incentives_and_rules",
   "calculate",
   "run_financial_model"
  ],
  "profile": {
   "building_name": "Jefferson Market Library (NYPL)",
   "address": "425 6th Avenue",
   "borough": "Manhattan",
   "building_type": "library",
   "floor_area_sqft": 18643,
   "year_built": 1877,
   "roof_type": "pitched",
   "roof_area_sqft": 7020,
   "annual_kwh": 268331,
   "budget_amount": 500000,
   "budget_year": 2027,
   "goal": "Cut grid electricity 30% by 2030",
   "existing_renewables": "none",
   "existing_efficiency": "none",
   "existing_solar_kw": null,
   "critical_loads": "reading room cooling and lighting",
   "utility": "Con Edison"
  },
  "scenarios": {
   "A": {
    "scenario_name": "Efficiency only",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 0.0,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     74572.0,
     149144.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     74572.0,
     149144.0
    ],
    "reduction_pct_of_use": [
     10.0,
     20.0
    ],
    "reaches_goal": false,
    "annual_savings_usd": [
     5316.0,
     12976.0
    ],
    "payback_years": [
     5.7,
     28.1
    ],
    "budget_strain": "within budget",
    "budget_gap_usd": [
     0.0,
     0.0
    ],
    "budget_note": "The estimated cost fits within the budget.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     0.0,
     0.0
    ],
    "solar_alone_exceeds_use": false
   }
  },
  "labelCounts": {
   "FACT": 13,
   "RECOMMENDATION": 18,
   "ESTIMATE": 8,
   "ASSUMPTION": 8
  },
  "claimTotal": 47,
  "summary": [
   "Goal: cut grid electricity 30% by 2030 on a $500,000 capital budget (budget year 2027), as you entered it.",
   "Can solar go on the roof? Not yet decided. The roof is pitched, and the sizing tools refuse to size a pitched roof until an engineer or roofer verifies the usable roof area. I therefore give no solar array size, output or savings, and I did not cost Scenarios B or C. The building is also a city landmark, so a Landmarks Preservation Commission (LPC) review is required before any rooftop work. I cannot certify that the roof can hold panels; a licensed PE or RA must do that analysis.",
   "Scenario A (standard efficiency only) is estimated to cost $74,572-$149,144 and to cut grid use 10-20%. That is 33-67% of the way to the 30% goal. It does not reach the goal and it fits within your budget.",
   "Rooftop solar alone could not reach 30% in any case, and efficiency alone does not either. Meeting the goal will most likely need deeper efficiency plus verified solar, and what that costs relative to $500,000 is not yet known. Whether to extend the budget is your decision once that gap is compared with the savings. I cannot guarantee savings; every figure is an estimate with a range."
  ],
  "building": [
   "Jefferson Market Library (NYPL), 425 6th Avenue, Manhattan; library; built 1877; 18,643 sq ft floor area; roof area 7,020 sq ft; pitched roof; Con Edison; annual grid use 268,331 kWh. These are the figures you entered.",
   "Existing systems: you entered no existing renewables and no existing efficiency work, so the plan assumes none and takes the full benchmark efficiency savings. If any LED, controls or other work is already done, tell me; that would lower the savings and my confidence in them. The baseline for the goal is the 268,331 kWh/yr the building buys from the grid.",
   "City records (PLUTO) list the lot at 421 Avenue of the Americas, a landmark, built 1877, one building with a 7,019 sq ft footprint, 3 floors, gross floor area 19,800 sq ft. The geocoder matched your address '425 6 Avenue'. The footprint is close to your 7,020 sq ft roof figure, but a footprint is ground area, not a measured roof.",
   "Your Greenwich Village Historic District statement is your own. I did not look up the district designation; only the landmark flag on the city lot record was checked."
  ],
  "assumptions": [
   "A7: Efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.",
   "A9: Planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open.",
   "A5: Incentive programs and rules come from a mock sample fixture, pending live verification.",
   "A6: Hazard ratings come from a mock sample fixture, pending site-specific assessment."
  ],
  "baseline": [
   "Baseline: 268,331 kWh/yr bought from the grid (from your bills/intake, 14.4 kWh per sq ft of your floor area).",
   "The 30% goal equals about 80,500 kWh/yr less grid use. Standard efficiency (LED and controls) is estimated to cut 26,833-53,666 kWh/yr, which is 10-20% of use.",
   "Estimated annual savings from Scenario A are $5,316-$12,976. This uses the New York commercial average price of $0.1981-$0.2418/kWh, not this building's own tariff.",
   "Start with LED lighting and controls, since you reported no efficiency work. In a 1877 landmark, interior work is generally easier to permit than exterior work, but confirm with LPC and your design team."
  ],
  "solar": [
   "Solar sizing refused: the roof is pitched, and the calculation tool will not size a pitched roof from flat-roof defaults. I give no usable roof area, array size, solar kWh or solar savings.",
   "Next step: have an engineer or roofer verify the usable roof area (size, pitch, direction, structure, shading) and enter it in the intake as verified_usable_roof_sqft, then re-plan. Also verify the 7,020 sq ft roof area you entered. Roof replacement year is blank; add it, because panels on a roof near end-of-life usually mean re-roofing first."
  ],
  "money": [
   "Net cost for Scenario A is $74,572-$149,144 with no incentive counted.",
   "Left out of net cost: the incentives tool returned only mock, stale sample data (retrieved 2025-10-01) listing a federal commercial ITC and a NYSERDA NY-Sun incentive as open. Because that data is a sample and out of date, both are treated as uncertain and are left out of net cost. Eligibility of a public library for a tax credit is also not verified. Confirm current status on official federal and NYSERDA pages before relying on either.",
   "Electricity price used: New York commercial average $0.1981-$0.2418/kWh (12-month average $0.222), EIA, effective 2026-07. This is not the building's own tariff.",
   "Because the full path to 30% is not yet costed, I cannot yet say whether $500,000 is enough. Efficiency at the deep benchmark saves 15-25%, which on its own stays below 30%, so some solar or other reduction is likely needed. Whether to extend the budget is your decision after comparing the gap with the savings."
  ],
  "phases": [
   "Phase 0, confirm data and budget: confirm the electric bills (268,331 kWh/yr), the budget year and type (2027 capital), the Con Edison tariff, the roof replacement year, and any existing efficiency work.",
   "Phase 1, professional reviews: a structural PE/RA analysis, a roof condition survey, and verification of the usable roof area. Begin LPC consultation early.",
   "Phase 2, efficiency measures: LED lighting and controls (Scenario A package), which can be done first and fit within the budget.",
   "Phase 3, permits and Con Edison interconnection application: LPC approval, NYC DOB permits, a licensed electrician, FDNY rooftop access review, and the Con Edison interconnection application. Do this only after the roof is verified.",
   "Phase 4, solar installation: only if the verified roof area, structural review and LPC approval support it; the array would be sized after re-planning.",
   "Phase 5, battery, commissioning and verification against bills: size a battery for the critical loads once solar is sized, then check actual results against 12 months of bills."
  ],
  "resilience": [
   "Critical loads: reading room cooling and lighting. Scenario A gives no backup power. Scenarios B and C were not run, so there is no battery sizing or outage-hours figure. Solar panels without a battery shut off during an outage, so solar alone would not keep the reading room running.",
   "Hazard context is a mock sample (rated flood zone X, low flood; heat and winter storm moderate) and its note refers to a Queens site, so it is not specific to this building. Treat it as unverified until a real FEMA flood-zone check is done. If the real zone is A, AE, AH, AO, V or VE, equipment must go above the design flood elevation."
  ],
  "referrals": [
   "Required: a structural PE/RA analysis (I cannot certify that the roof can hold panels), a roof condition survey, a licensed electrician, FDNY rooftop access review, and a Con Edison interconnection review.",
   "Landmark review: the city lot record flags this building as a landmark. A Landmarks Preservation Commission (LPC) review is needed before any rooftop or exterior work, including visibility of panels from the street in a historic district. Ask whether the lot is on parkland; if it is, an LPC advisory report to the owning agency applies and counsel must do a parkland use review. The records returned no parkland flag.",
   "Pitched roof: output depends on the roof's pitch and direction; a PE or roofer must verify it before any solar sizing."
  ],
  "gaps": [
   "Failed or refused tool: the calculation tool (C1) refused to size solar because the roof is pitched and no verified usable roof area exists. Missing because of this: the usable roof area, array size, solar output, solar savings, and Scenarios B and C. The solar production tool was not called, since it would refuse for the same reason. Re-run once verified_usable_roof_sqft is entered.",
   "Scenario A was run with placeholder solar inputs because the model requires them; they are zero and do not affect Scenario A, which has no solar.",
   "Address mismatch: you gave 425 6th Avenue; the city lot record lists 421 Avenue of the Americas (it may be another frontage of the same lot). Please confirm. City gross floor area is 19,800 sq ft versus your 18,643 sq ft; I kept your figure.",
   "Mock and stale data: the hazard, tariff and incentive results are saved sample data from 2025-10-01, and are stale. They are not presented as facts, and their confidence is low. The tariff is a best match named SC-9 Rate I (General Large), effective 2025-07-01, and is not confirmed against a bill; please confirm it. The price used is a statewide average, not this building's tariff.",
   "Roof replacement year is missing from the intake, so the roof's remaining life is unknown. The roof area is your number and should be verified by an engineer or roofer.",
   "Efficiency savings rest on a published benchmark range (A7) rather than a building model, so confidence is low; an energy audit would firm it up. Payback is a simple payback, not the full SAM model."
  ],
  "sources": [
   "Intake profile (user-entered).",
   "NYC PLUTO tax lot data (building record, landmark flag, footprint).",
   "EIA electricity data browser (New York commercial price).",
   "Scenario A calculation F-A (run_financial_model, planning-level, not quotes)."
  ],
  "flags": [
   "missing_field:roof_replaced_year",
   "address_street_mismatch",
   "mock_data_in_live_run",
   "stale_data",
   "statewide_average_rate",
   "tariff_needs_user_confirmation",
   "tool_error:calculate"
  ],
  "siteContext": {
   "roof_kind": "non_flat",
   "landmark": true,
   "flood_zone": "X"
  },
  "copy": {
   "outcome": "Needs a roofer first",
   "tone": "next-step",
   "headline": "One step first: get your roof checked.",
   "subhead": "The roof is pitched, with a clock tower, so we won't guess how much solar fits. Efficiency alone can cut 10 to 20 percent for about $75k to $149k. Solar waits for your engineer or roofer.",
   "recommended": "A",
   "next": {
    "title": "Have an engineer or roofer verify the usable roof area",
    "body": "Enter the verified area and we will re-plan with solar. As a landmark in a historic district, any rooftop work also needs a Landmarks Preservation Commission review."
   },
   "incentives": null
  }
 },
 {
  "id": "real4_ps24_bronx_existing_solar",
  "label": "P.S. 24, Bronx",
  "kind": "recorded",
  "tag": "Roof already full of solar: efficiency only",
  "question": "How do we cut our grid power another 30% by 2030 on a $400k capital budget?",
  "status": "partial",
  "toolCalls": 10,
  "events": 53,
  "tools": [
   "get_building_profile",
   "lookup_ny_building_records",
   "calculate",
   "calculate",
   "get_solar_production",
   "get_utility_rates",
   "get_utility_tariff",
   "search_ny_incentives_and_rules",
   "get_hazard_context",
   "run_financial_model"
  ],
  "profile": {
   "building_name": "P.S. 24 (X024)",
   "address": "660 West 236th Street",
   "borough": "Bronx",
   "building_type": "elementary school",
   "floor_area_sqft": 115325,
   "year_built": 1953,
   "roof_type": "flat",
   "roof_area_sqft": 40500,
   "annual_kwh": 226605,
   "budget_amount": 400000,
   "budget_year": 2027,
   "goal": "Cut grid electricity 30% by 2030",
   "existing_renewables": "none",
   "existing_efficiency": "none",
   "existing_solar_kw": 380,
   "critical_loads": "emergency lighting and communications",
   "utility": "Con Edison"
  },
  "scenarios": {
   "A": {
    "scenario_name": "Efficiency only",
    "package": {
     "efficiency_level": "standard",
     "solar_kw_dc": 0.0,
     "battery_kwh": 0.0
    },
    "upfront_usd": [
     461300.0,
     922600.0
    ],
    "incentives_counted_usd": [
     0.0,
     0.0
    ],
    "net_cost_usd": [
     461300.0,
     922600.0
    ],
    "reduction_pct_of_use": [
     10.0,
     20.0
    ],
    "reaches_goal": false,
    "annual_savings_usd": [
     4489.0,
     10959.0
    ],
    "payback_years": [
     42.1,
     205.5
    ],
    "budget_strain": "over budget",
    "budget_gap_usd": [
     61300.0,
     522600.0
    ],
    "budget_note": "The estimated cost is $61,300-$522,600 more than your budget, and it does not reach the goal at the low end.",
    "outage_hours": [
     0.0,
     0.0
    ],
    "surplus_solar_kwh": [
     0.0,
     0.0
    ],
    "solar_alone_pct_of_use": [
     0.0,
     0.0
    ],
    "solar_alone_exceeds_use": false
   }
  },
  "labelCounts": {
   "FACT": 13,
   "ESTIMATE": 16,
   "RECOMMENDATION": 18,
   "ASSUMPTION": 11
  },
  "claimTotal": 58,
  "summary": [
   "Your goal is to cut grid electricity 30% by 2030 on a $400,000 capital budget (budget year 2027).",
   "The existing 380 kW rooftop array already fills the whole usable roof (about 338 kW estimated by the roof-sizing formulas), so there is no free roof for new solar. The plan therefore rests on efficiency. Scenarios B and C depend on new solar and were not costed.",
   "Scenario A (standard efficiency, no new solar) could cut grid use by about 10-20% of annual use. That is about 33-67% of the 30% goal. It does not reach the goal at the low end.",
   "Scenario A is estimated at $461,300-$922,600 upfront. That costs $61,300-$522,600 more than your $400,000 budget. Meeting the goal may take more than the budget. Whether to extend it is your decision once you compare the gap with the savings.",
   "Start with a metered or audited look at where the building uses power. Then decide on a staged efficiency program and a possible budget increase. The standard package alone is not likely to deliver 30%."
  ],
  "building": [
   "P.S. 24 (X024), an elementary school at 660 West 236th Street, Bronx. Built 1953, flat roof, entered roof area 40,500 sq ft, entered floor area 115,325 sq ft, Con Edison customer. These are your entries.",
   "The city record (PLUTO) lists gross floor area 135,600 sq ft against your 115,325 sq ft (intake_mismatch:floor_area_sqft). I kept your figure as the working number. Please confirm which is right. A larger floor area would raise the benchmark efficiency cost.",
   "The city's address for this lot is 660 West 235 Street, not 236th Street (address_street_mismatch). It may be another frontage of the same lot. Please confirm it is your building.",
   "City building footprints total about 40,497 sq ft on the lot, close to your 40,500 sq ft roof. A footprint is ground area, not a measured roof, so verify the roof area with an engineer or roofer.",
   "Existing systems taken into account: a 380 kW solar array already on the roof. No other renewables and no efficiency work already done, as you entered. The goal baseline is the electricity the building buys from the grid, which the existing solar already lowers."
  ],
  "assumptions": [
   "A2: Usable roof setback factor 0.55 (C1).",
   "A3: Array density factor 66 sq ft/kW DC (C2).",
   "A5: Incentive programs and rules come from a mock sample fixture, pending live verification.",
   "A6: Hazard ratings come from a mock sample fixture, pending site-specific assessment.",
   "A7: Efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.",
   "A9: Planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open."
  ],
  "baseline": [
   "Baseline: the building buys about 226,605 kWh a year from the grid (from your bills as entered). A 30% cut is about 68,000 kWh a year.",
   "Standard efficiency (LED lighting and controls) might reduce use by about 22,660-45,321 kWh a year, or 10-20% of annual use. It is a benchmark, not a building model.",
   "You reported no efficiency work done yet, so LED and controls are treated as open measures. If any were already installed, the savings and confidence would be lower. Please confirm.",
   "The date the roof was last replaced is missing (missing_field:roof_replaced_year). Please provide it. It affects roof condition and any work on the roof."
  ],
  "solar": [
   "Usable roof area, using setback factor 0.55, is about 22,275 sq ft.",
   "The array that fits that usable roof is about 337.5 kW DC. Your existing 380 kW array already uses it all, so there is no free roof for a new array.",
   "The solar production tool refused to run because the existing array already uses the whole usable roof. I give no new-solar output, no new-solar savings, and no cost for scenarios B and C. Rooftop solar alone cannot reach your goal here.",
   "Have an engineer or roofer verify the roof area, the existing array's actual size and output, and any free roof area, such as over stairwells or a second building. Re-plan if more space turns up."
  ],
  "money": [
   "Scenario A is estimated at $461,300-$922,600 upfront, using planning-level benchmark prices of $4-8 per sq ft on your entered floor area. The $400,000 capital budget does not cover it. Meeting the goal may take more than the budget. Whether to extend it is your decision once you compare the gap with the savings.",
   "If the city's larger floor area of 135,600 sq ft is correct, the benchmark efficiency cost would be higher than shown. I did not re-run the model.",
   "Left out of net cost: the Federal ITC (commercial) and a NY-Sun commercial incentive are listed as open in saved sample data, retrieved 2025-10-01 and stale. They are mock data and apply to solar, which this plan does not add. No incentive is counted in net cost.",
   "Electricity price used: $0.1981-$0.2418 per kWh, 12-month average $0.222. This is the New York commercial average, not your own tariff. Annual savings are about $4,489-$10,959.",
   "Tariff on file: Con Edison SC-9 Rate I (General Large), effective 2025-07-01. It is stale, mock sample data that needs your confirmation against a bill. Energy charge $0.20-$0.24 per kWh and demand charge $18-$24 per kW-month. It is not used in the savings figures."
  ],
  "phases": [
   "Phase 0, confirm data and budget: gather 12 months of Con Edison bills and confirm grid use and tariff. Confirm floor area (115,325 vs 135,600 sq ft). Confirm the budget year and type, and whether it can be extended. Confirm the existing array's size and output, and the roof replacement year.",
   "Phase 1, professional reviews: a structural PE/RA review and a roof condition survey before any rooftop work. I cannot certify that the roof can hold equipment.",
   "Phase 2, efficiency measures: commission an energy audit. Then install LED lighting and controls first, staged to fit the budget, and size further measures from the audit.",
   "Phase 3, permits and Con Edison: a licensed electrician pulls permits for the electrical work. Arrange FDNY rooftop access, and have Con Edison review any change to the existing interconnection.",
   "Phase 4, solar installation: no new array is planned because there is no free roof. Keep the existing array in good order, and revisit if verified free area is found.",
   "Phase 5, battery, commissioning and verification: compare measured grid use against bills after the work, to check the real reduction against the 30% goal. Consider a battery for critical loads only after the other reviews."
  ],
  "resilience": [
   "Scenario A gives no backup power: 0 outage hours. Scenario B was not modeled. Solar panels shut off in an outage without a battery, so the existing array does not power the building in a blackout. Scenario C, with a battery, was not costed and no outage hours are given.",
   "Critical loads named in your intake: emergency lighting and communications. I did not size a battery, since Scenario C was not costed. A battery for these loads can be sized separately.",
   "Sample hazard ratings: flood zone X, flood rating low, heat and winter storm moderate. This is saved sample data, and its note refers to a Queens site, not the Bronx. Confirm with a site-specific flood review. No flood-zone review is triggered by these sample ratings."
  ],
  "referrals": [
   "Required reviews: a structural PE/RA analysis, a roof condition survey, a licensed electrician, FDNY rooftop access, and a Con Edison interconnection review. I cannot certify the roof; a licensed PE or RA must do the structural analysis.",
   "The city record shows no landmark flag for this lot, so no Landmarks Preservation Commission review is triggered. The records do not show parkland, so no parkland review is triggered either. Confirm both."
  ],
  "gaps": [
   "The PVWatts solar production call failed because the existing 380 kW array already uses the whole usable roof. Missing: new-solar output, new-solar savings, and the costs of scenarios B and C. Next step: re-run if verified free roof area is found.",
   "Intake and city records disagree on floor area (115,325 vs 135,600 sq ft), and the city lists the address as 235th Street. I used your values. Please confirm both.",
   "Data question: the annual output you reported for the existing array looks larger than the building's grid purchases of 226,605 kWh. Please confirm that 226,605 kWh is what the building buys from the grid after the solar, since the 30% goal is measured against it.",
   "The price is the New York commercial statewide average, not your tariff (statewide_average_rate). The Con Edison SC-9 tariff is stale mock sample data and needs your confirmation (tariff_needs_user_confirmation, mock_data_in_live_run).",
   "Incentive and hazard data are saved sample data (mock_data_in_live_run, stale_data), retrieved 2025-10-01. They are not live, and no incentive is counted in net cost.",
   "The roof replacement year is missing (missing_field:roof_replaced_year). Efficiency savings are benchmark ranges and confidence is low. Scenario A was run with no solar output because no free roof exists. Payback is a simple payback, not the full SAM model."
  ],
  "sources": [
   "Building entries: session://profile.",
   "NYC building records (PLUTO, dataset pluto-26v2, retrieved 2026-10-15).",
   "EIA New York commercial electricity price (dataset eia-retail-sales-2026-07, retrieved 2026-10-15).",
   "Calculations C1, C2 and F-A from the planning tools. Mock sample sources used, flagged above: tariff, incentives and hazard."
  ],
  "flags": [
   "missing_field:roof_replaced_year",
   "intake_mismatch:floor_area_sqft",
   "address_street_mismatch",
   "tool_error:get_solar_production",
   "statewide_average_rate",
   "tariff_needs_user_confirmation",
   "stale_data",
   "mock_data_in_live_run"
  ],
  "siteContext": {
   "roof_kind": "flat",
   "existing_systems": "solar 380 kW making about 457,512 kWh a year",
   "flood_zone": "X"
  },
  "copy": {
   "outcome": "Roof already full: efficiency only",
   "tone": "next-step",
   "headline": "Your roof is already full of solar, so the next gains are efficiency.",
   "subhead": "Your 380 kW array already uses the usable roof, so there is no room for a second one. Standard efficiency could cut 10 to 20 percent, but at this building's size it costs more than your $400,000.",
   "recommended": "A",
   "next": {
    "title": "Send the existing array's size and how its output is credited",
    "body": "The array makes more power than the building buys from the grid. Knowing how that output is used or credited could change the baseline, and there may be roof area we can't see."
   },
   "incentives": null
  }
 }
] as MockSample[];
