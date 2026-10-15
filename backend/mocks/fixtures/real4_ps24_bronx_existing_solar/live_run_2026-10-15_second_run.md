<!-- Live run, second pass, 2026-10-15, after the roof/existing-systems/budget changes: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, footprints, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools answered from case 1's saved samples. Status partial: Check 4 rejected this plan on a false positive (it treated the user's own existing-array kWh as an invented solar figure). That bug is fixed and this stored plan re-checks as passing. The plan itself concludes the existing 380 kW array already fills the usable roof. Tool calls: 10, 120.1 s. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **FACT** (high): Your goal is to cut grid electricity 30% by 2030 on a $400,000 capital budget (budget year 2027). [400,000 USD] — source/calc: `session://profile`
- **ESTIMATE** (medium): The existing 380 kW rooftop array already fills the whole usable roof (about 338 kW estimated by the roof-sizing formulas), so there is no free roof for new solar. The plan therefore rests on efficiency. Scenarios B and C depend on new solar and were not costed. [337.5 kW DC] — source/calc: `C2`
- **ESTIMATE** (low): Scenario A (standard efficiency, no new solar) could cut grid use by about 10-20% of annual use. That is about 33-67% of the 30% goal. It does not reach the goal at the low end. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario A is estimated at $461,300-$922,600 upfront. That costs $61,300-$522,600 more than your $400,000 budget. Meeting the goal may take more than the budget. Whether to extend it is your decision once you compare the gap with the savings. [61,300–522,600 USD above budget] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Start with a metered or audited look at where the building uses power. Then decide on a staged efficiency program and a possible budget increase. The standard package alone is not likely to deliver 30%. — source/calc: `F-A`

## 2. Building profile and data provenance

- **FACT** (high): P.S. 24 (X024), an elementary school at 660 West 236th Street, Bronx. Built 1953, flat roof, entered roof area 40,500 sq ft, entered floor area 115,325 sq ft, Con Edison customer. These are your entries. — source/calc: `session://profile`
- **FACT** (medium): The city record (PLUTO) lists gross floor area 135,600 sq ft against your 115,325 sq ft (intake_mismatch:floor_area_sqft). I kept your figure as the working number. Please confirm which is right. A larger floor area would raise the benchmark efficiency cost. [115,325–135,600 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): The city's address for this lot is 660 West 235 Street, not 236th Street (address_street_mismatch). It may be another frontage of the same lot. Please confirm it is your building. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): City building footprints total about 40,497 sq ft on the lot, close to your 40,500 sq ft roof. A footprint is ground area, not a measured roof, so verify the roof area with an engineer or roofer. [40,497 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): Existing systems taken into account: a 380 kW solar array already on the roof. No other renewables and no efficiency work already done, as you entered. The goal baseline is the electricity the building buys from the grid, which the existing solar already lowers. [380 kW] — source/calc: `session://profile`

## 3. Assumptions register

- **ASSUMPTION** (medium) [A2]: A2: Usable roof setback factor 0.55 (C1). — optional source/calc: `C1`
- **ASSUMPTION** (medium) [A3]: A3: Array density factor 66 sq ft/kW DC (C2). — optional source/calc: `C2`
- **ASSUMPTION** (low) [A5]: A5: Incentive programs and rules come from a mock sample fixture, pending live verification.
- **ASSUMPTION** (low) [A6]: A6: Hazard ratings come from a mock sample fixture, pending site-specific assessment.
- **ASSUMPTION** (low) [A7]: A7: Efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.
- **ASSUMPTION** (low) [A9]: A9: Planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open. — optional source/calc: `F-A`

## 4. Baseline and efficiency opportunities

- **FACT** (medium): Baseline: the building buys about 226,605 kWh a year from the grid (from your bills as entered). A 30% cut is about 68,000 kWh a year. [226,605 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (low): Standard efficiency (LED lighting and controls) might reduce use by about 22,660-45,321 kWh a year, or 10-20% of annual use. It is a benchmark, not a building model. [22,660–45,321 kWh/yr] — source/calc: `F-A`
- **RECOMMENDATION** (medium): You reported no efficiency work done yet, so LED and controls are treated as open measures. If any were already installed, the savings and confidence would be lower. Please confirm. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): The date the roof was last replaced is missing (missing_field:roof_replaced_year). Please provide it. It affects roof condition and any work on the roof. — source/calc: `session://profile`

## 5. Solar assessment with calculations

- **ESTIMATE** (medium): Usable roof area, using setback factor 0.55, is about 22,275 sq ft. [22,275 sq ft] — source/calc: `C1`
- **ESTIMATE** (medium): The array that fits that usable roof is about 337.5 kW DC. Your existing 380 kW array already uses it all, so there is no free roof for a new array. [337.5 kW DC] — source/calc: `C2`
- **RECOMMENDATION** (high): The solar production tool refused to run because the existing array already uses the whole usable roof. I give no new-solar output, no new-solar savings, and no cost for scenarios B and C. Rooftop solar alone cannot reach your goal here. — source/calc: `C2`
- **RECOMMENDATION** (medium): Have an engineer or roofer verify the roof area, the existing array's actual size and output, and any free roof area, such as over stairwells or a second building. Re-plan if more space turns up. — source/calc: `C1`

## 6. Scenario comparison table

- **ESTIMATE** (low): Scenario A (efficiency only): reduction of 10-20% of annual use, 33-67% of the goal. It does not reach the 30% goal at the low end. Rooftop solar alone adds 0% because no new solar is planned. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario A upfront and net cost: $461,300-$922,600. Nothing is counted as an incentive. [461,300–922,600 USD] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario A costs $61,300-$522,600 more than your budget, and it does not reach the goal at the low end. Budget strain is over budget, at 1.15 to 2.31 times the budget. [61,300–522,600 USD above budget] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario A simple payback: about 42.1-205.5 years on annual savings of about $4,489-$10,959. This is a simple payback, not the full SAM model. [42.1–205.5 years] — source/calc: `F-A`
- **ESTIMATE** (medium): Scenario A outage hours: 0. It gives no backup power. [0 hours] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Scenarios B (efficiency plus solar within budget) and C (deep efficiency, full solar and battery) were not costed. Both depend on a new array and there is no free roof. They can be compared if verified free roof area is found. — source/calc: `C2`

## 7. Cost, financing and incentives

- **ESTIMATE** (low): Scenario A is estimated at $461,300-$922,600 upfront, using planning-level benchmark prices of $4-8 per sq ft on your entered floor area. The $400,000 capital budget does not cover it. Meeting the goal may take more than the budget. Whether to extend it is your decision once you compare the gap with the savings. [461,300–922,600 USD] — source/calc: `F-A`
- **RECOMMENDATION** (low): If the city's larger floor area of 135,600 sq ft is correct, the benchmark efficiency cost would be higher than shown. I did not re-run the model. — source/calc: `F-A`
- **ASSUMPTION** (low) [A5]: Left out of net cost: the Federal ITC (commercial) and a NY-Sun commercial incentive are listed as open in saved sample data, retrieved 2025-10-01 and stale. They are mock data and apply to solar, which this plan does not add. No incentive is counted in net cost. — optional source/calc: `https://example.test/fictional/incentives-v0`
- **ESTIMATE** (medium): Electricity price used: $0.1981-$0.2418 per kWh, 12-month average $0.222. This is the New York commercial average, not your own tariff. Annual savings are about $4,489-$10,959. [4,489–10,959 USD/yr] — source/calc: `F-A`
- **ASSUMPTION** (low) [A5]: Tariff on file: Con Edison SC-9 Rate I (General Large), effective 2025-07-01. It is stale, mock sample data that needs your confirmation against a bill. Energy charge $0.20-$0.24 per kWh and demand charge $18-$24 per kW-month. It is not used in the savings figures. — optional source/calc: `https://example.test/fictional/openei-tariff-v2`

## 8. Priority roadmap

- **RECOMMENDATION** (medium): Phase 0, confirm data and budget: gather 12 months of Con Edison bills and confirm grid use and tariff. Confirm floor area (115,325 vs 135,600 sq ft). Confirm the budget year and type, and whether it can be extended. Confirm the existing array's size and output, and the roof replacement year. — source/calc: `session://profile`
- **RECOMMENDATION** (high): Phase 1, professional reviews: a structural PE/RA review and a roof condition survey before any rooftop work. I cannot certify that the roof can hold equipment. — source/calc: `session://profile`
- **RECOMMENDATION** (low): Phase 2, efficiency measures: commission an energy audit. Then install LED lighting and controls first, staged to fit the budget, and size further measures from the audit. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and Con Edison: a licensed electrician pulls permits for the electrical work. Arrange FDNY rooftop access, and have Con Edison review any change to the existing interconnection. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 4, solar installation: no new array is planned because there is no free roof. Keep the existing array in good order, and revisit if verified free area is found. — source/calc: `C2`
- **RECOMMENDATION** (low): Phase 5, battery, commissioning and verification: compare measured grid use against bills after the work, to check the real reduction against the 30% goal. Consider a battery for critical loads only after the other reviews. — source/calc: `F-A`

## 9. Resilience and reliability plan

- **ESTIMATE** (medium): Scenario A gives no backup power: 0 outage hours. Scenario B was not modeled. Solar panels shut off in an outage without a battery, so the existing array does not power the building in a blackout. Scenario C, with a battery, was not costed and no outage hours are given. [0 hours] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Critical loads named in your intake: emergency lighting and communications. I did not size a battery, since Scenario C was not costed. A battery for these loads can be sized separately. — source/calc: `session://profile`
- **ASSUMPTION** (low) [A6]: Sample hazard ratings: flood zone X, flood rating low, heat and winter storm moderate. This is saved sample data, and its note refers to a Queens site, not the Bronx. Confirm with a site-specific flood review. No flood-zone review is triggered by these sample ratings. — optional source/calc: `https://example.test/fictional/hazard-v0`

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): Required reviews: a structural PE/RA analysis, a roof condition survey, a licensed electrician, FDNY rooftop access, and a Con Edison interconnection review. I cannot certify the roof; a licensed PE or RA must do the structural analysis. — source/calc: `session://profile`
- **FACT** (medium): The city record shows no landmark flag for this lot, so no Landmarks Preservation Commission review is triggered. The records do not show parkland, so no parkland review is triggered either. Confirm both. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`

## 11. Path to net-zero and learning resources

- **RECOMMENDATION** (low): Rooftop solar cannot close the gap, since the roof is full. Getting to 30% will rest on efficiency, and the standard package at 10-20% falls short at the low end. Ask the energy audit to identify deeper measures such as HVAC, controls and the building envelope. Net-zero would need more than efficiency and the existing roof array. — source/calc: `F-A`
- **ASSUMPTION** (low) [A5]: No learning resources were returned by the tools in this run.

## 12. Gaps, conflicts and confidence summary

- **RECOMMENDATION** (high): The PVWatts solar production call failed because the existing 380 kW array already uses the whole usable roof. Missing: new-solar output, new-solar savings, and the costs of scenarios B and C. Next step: re-run if verified free roof area is found. — source/calc: `C2`
- **FACT** (medium): Intake and city records disagree on floor area (115,325 vs 135,600 sq ft), and the city lists the address as 235th Street. I used your values. Please confirm both. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (medium): Data question: the annual output you reported for the existing array looks larger than the building's grid purchases of 226,605 kWh. Please confirm that 226,605 kWh is what the building buys from the grid after the solar, since the 30% goal is measured against it. — source/calc: `session://profile`
- **FACT** (low): The price is the New York commercial statewide average, not your tariff (statewide_average_rate). The Con Edison SC-9 tariff is stale mock sample data and needs your confirmation (tariff_needs_user_confirmation, mock_data_in_live_run). — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ASSUMPTION** (low) [A5]: Incentive and hazard data are saved sample data (mock_data_in_live_run, stale_data), retrieved 2025-10-01. They are not live, and no incentive is counted in net cost. — optional source/calc: `https://example.test/fictional/incentives-v0`
- **ESTIMATE** (low): The roof replacement year is missing (missing_field:roof_replaced_year). Efficiency savings are benchmark ranges and confidence is low. Scenario A was run with no solar output because no free roof exists. Payback is a simple payback, not the full SAM model. — source/calc: `F-A`

## 13. Sources

- **FACT** (high): Building entries: session://profile. — source/calc: `session://profile`
- **FACT** (high): NYC building records (PLUTO, dataset pluto-26v2, retrieved 2026-10-15). — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): EIA New York commercial electricity price (dataset eia-retail-sales-2026-07, retrieved 2026-10-15). — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ESTIMATE** (medium): Calculations C1, C2 and F-A from the planning tools. Mock sample sources used, flagged above: tariff, incentives and hazard. — source/calc: `F-A`

---
*All cost, savings and payback figures are planning-level ESTIMATE ranges, not quotes, and not a guarantee of savings. Scenarios B and C were not costed because the roof has no free space for new solar. Re-plan once the open questions in section 12 are answered.*
