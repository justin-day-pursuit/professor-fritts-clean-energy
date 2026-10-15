<!-- Live run on 2026-10-15: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools have no live version and answered from case 1's saved samples (so the hazard note says Queens). Status done; Check 4 passed on the first try. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **FACT** (high): Goal: cut grid electricity 30% by 2030 on a $400,000 capital budget (budget year 2027). On the 226,605 kWh/yr you buy from the grid, 30% is about 67,980 kWh/yr. [67,982 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (low): Scenario A (standard efficiency only) is estimated to cut about 10-20% of annual use (22,660-45,321 kWh/yr). That is roughly 33-67% of the 30% goal, so it does not reach the goal on its own. At planning-level benchmark prices its upfront cost ($461,300-$922,600) is over your $400,000 budget. [33–67 % of goal] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (efficiency plus solar within budget) came back identical to A. Efficiency alone already uses up the budget at the benchmark prices, so the tool left no money for new solar. — source/calc: `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency, whole-roof solar, 960 kWh battery) is estimated at $2.68M-$4.23M upfront, about 6.7-10.6 times your budget. The tool's 181-208% reduction treats the whole-roof array as new solar, so it likely double counts the array you already have. I do not rely on that figure. [2,679,250–4,230,200 USD upfront] — source/calc: `F-C`
- **RECOMMENDATION** (medium): Biggest open question: your existing array made about 457,000 kWh last year. That is more than my PVWatts estimate for the whole usable roof (377,102-414,398 kWh/yr). The roof may have little free space for more solar. Please send the existing array size (kW), its install date, and whether the 457,000 kWh is used on site, exported, or credited to other accounts. — source/calc: `C2`

## 2. Building profile and data provenance

- **FACT** (high): P.S. 24 (X024), elementary school, 660 West 236th Street, Bronx; built 1953; flat roof of 38,000 sq ft; Con Edison customer; critical loads are emergency lighting and communications. You entered 115,325 sq ft floor area and 226,605 kWh/yr bought from the grid. — source/calc: `session://profile`
- **FACT** (high): The NYC PLUTO record shows gross floor area of 135,600 sq ft and lot area of 140,975 sq ft, against your 115,325 sq ft. The lot size does not match your floor area. I kept your 115,325 sq ft as the working figure. Please confirm which is right. Efficiency costs scale with floor area, so the larger figure would raise Scenario A's cost. [115,325–135,600 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): The city record lists the lot as 660 WEST 235 STREET (ZIP 10471). You gave 660 West 236th Street. The geocoder matched 660 West 236 Street (ZIP 10463). It may be another frontage of the same lot (BBL 2059170140). Please confirm the address. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): Roof replacement year was left blank on the intake, so roof age and condition are unknown. — source/calc: `session://profile`

## 3. Assumptions register

- **ASSUMPTION** (medium) [A1]: A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ASSUMPTION** (medium) [A2]: A2: usable roof setback factor 0.55 (C1).
- **ASSUMPTION** (medium) [A3]: A3: array density factor 66 sq ft per kW DC (C2).
- **ASSUMPTION** (low) [A4]: A4: the battery size is a sample (fictional REopt stand-in sized for 8 hours of cooling-center backup), not a site design.
- **ASSUMPTION** (low) [A5]: A5: incentive programs and rules come from a mock sample fixture, pending live verification.
- **ASSUMPTION** (low) [A6]: A6: hazard ratings come from a mock sample fixture, pending a site-specific assessment.
- **ASSUMPTION** (medium) [A7]: A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.
- **ASSUMPTION** (low) [A9]: A9: planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open.

## 4. Baseline and efficiency opportunities

- **FACT** (medium): Baseline: 226,605 kWh/yr bought from the grid, from your bills. About 1.97 kWh per sq ft on your floor area. Your total building use is higher if part of the 457,000 kWh from the existing array is used on site. I have not added it, because I don't know how much is used on site. [226,605 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (low): Standard efficiency (LED and controls) is estimated to cut 10-20% of annual use, 22,660-45,321 kWh/yr. This is a benchmark range, not a building model or an audit. [22,660–45,321 kWh/yr] — source/calc: `F-A`
- **RECOMMENDATION** (low): Efficiency alone is unlikely to reach 30% at the standard level. The gap to the goal is roughly 22,660-45,320 kWh/yr. Closing it needs deeper measures or more solar. Your $400,000 is below the benchmark cost of a whole-building standard package. — source/calc: `F-A`

## 5. Solar assessment with calculations

- **ESTIMATE** (low): Usable roof after setbacks: 38,000 sq ft x 0.55 = 20,900 sq ft. This assumes an empty roof, with no existing array. [20,900 sq ft] — source/calc: `C1`
- **ESTIMATE** (low): Full-roof array size: about 316.7 kW DC (20,900 sq ft / 66 sq ft per kW). [316.7 kW DC] — source/calc: `C2`
- **ESTIMATE** (medium): PVWatts output for that array is 377,102-414,398 kWh/yr, central 395,756. This is a whole-roof model and does not account for your existing panels. [377,102–414,398 kWh/yr] — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **ASSUMPTION** (medium) [A1]: The range reflects the loss band in A1.
- **ESTIMATE** (low): Taken at face value, that output is about 175% of your grid use (central). But your existing array already produces about 457,000 kWh/yr, above the model's whole-roof estimate. So the model's 166-183% 'solar alone' figure and its 'reaches goal' flag do not apply here, and I don't read them as evidence that more solar fits. [1.746 fraction of use (central)] — source/calc: `C3`
- **ESTIMATE** (low): If a whole-roof array were new, value at EIA prices would be $74,704-$100,202 per year (central $87,858 at the 12-month average price). Treat this as an upper bound that is probably not available to you. [74,704–100,202 USD/yr] — source/calc: `C4`

## 6. Scenario comparison table

- **ESTIMATE** (low): Scenario A (efficiency only): reduction 10-20% of use, 33-67% of the goal; upfront and net cost $461,300-$922,600; payback 42-206 years; over budget (1.15-2.31 times); outage backup 0 hours. Does not reach the goal. [461,300–922,600 USD net cost] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (efficiency plus solar within budget): same result as A, with no solar added because efficiency alone is over budget. Reduction 10-20%, 33-67% of goal; net cost $461,300-$922,600; payback 42-206 years; over budget; outage backup 0 hours. Does not reach the goal. [461,300–922,600 USD net cost] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency, 316.7 kW whole-roof solar, 960 kWh battery): upfront and net cost $2,679,250-$4,230,200; payback 23.5-51.9 years; over budget (6.7-10.6 times); outage hours 6.8-8.0. The tool reports the goal as reached (reduction 181-208% of use). That is not credible, because it counts a whole-roof array as new next to your existing one. Even so, the cost is far above $400,000. [2,679,250–4,230,200 USD net cost] — source/calc: `F-C`
- **ESTIMATE** (low): Paybacks are simple paybacks (cost divided by annual bill savings), not the full SAM model. Savings use statewide average prices, not your tariff. — source/calc: `F-A`

## 7. Cost, financing and incentives

- **ASSUMPTION** (low) [A9]: Costs use planning-level benchmark prices, not quotes (see A9). None of them are bids.
- **FACT** (low): Net cost counts no incentives. The tool listed a federal commercial ITC (status 'open', placed-in-service deadline 2027-12-31) and a NYSERDA NY-Sun commercial incentive. Both come from a fictional sample fixture last retrieved 2025-10-01, which is stale (the freshness limit is 7 days). They are uncertain and left out of net cost. I could not refresh them or verify them against official pages in this run. — source/calc: `https://example.test/fictional/incentives-v0`
- **RECOMMENDATION** (low): Treat your public-building tax status as unconfirmed. Ask a tax adviser whether any federal credit can apply to a public school before counting it. — source/calc: `https://example.test/fictional/incentives-v0`
- **FACT** (medium): Electricity price: EIA New York commercial average of $0.1981-$0.2418/kWh (12-month average $0.222), through 2026-07. This is a statewide average, not your tariff. [0.1981–0.2418 USD/kWh] — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **FACT** (low): Sample tariff: Con Edison SC-9 Rate I (General Large), effective 2025-07-01, energy $0.20-$0.24/kWh and demand $18-$24/kW-month. It is a best-match sample (mock, stale), not confirmed against a bill. Please confirm your tariff. — source/calc: `https://example.test/fictional/openei-tariff-v2`

## 8. Priority roadmap

- **RECOMMENDATION** (medium): Phase 0, confirm data and budget: send 12 months of bills, the existing array size and how its output is used or credited, your tariff, the correct floor area and address, and whether the $400,000 is a 2027 capital budget that can be split across years. — source/calc: `session://profile`
- **RECOMMENDATION** (high): Phase 1, professional reviews: a licensed structural PE/RA must analyze the roof, including the load of the existing panels, and a roof condition survey must cover roof age (replacement year unknown). I cannot certify that the roof can hold more panels. — source/calc: `C1`
- **RECOMMENDATION** (low): Phase 2, efficiency measures: commission an energy audit, then spend the $400,000 on the best-return measures first (LED and controls). This is the main way to approach the goal within budget. Standard measures at benchmark prices are estimated to deliver 33-67% of the goal. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and Con Edison interconnection: file the permits and the Con Edison interconnection application for any array change. This needs a licensed electrician and FDNY rooftop access review. — source/calc: `C2`
- **RECOMMENDATION** (low): Phase 4, solar installation: add panels only if the PE/RA and a layout of the existing array show free roof area. The current evidence suggests little or none. — source/calc: `C1`
- **RECOMMENDATION** (low): Phase 5, battery, commissioning and verification: consider a battery for emergency lighting and communications only once funding exists, then check results against bills. The 960 kWh sample is far larger than those loads may need; size it from a real critical-load study. — source/calc: `F-C`

## 9. Resilience and reliability plan

- **ESTIMATE** (low): Scenario C's sample battery (960 kWh, 120 kW) is estimated to cover critical loads for 6.8-8.0 hours. [6.8–8 hours] — source/calc: `F-C`
- **ASSUMPTION** (low) [A4]: Battery size is a sample sized for 8 hours of cooling-center backup, not a design.
- **ESTIMATE** (medium): Scenarios A and B give no backup power. Solar panels shut off during an outage unless a battery and islanding-capable inverters are installed, so your existing array likely gives no backup today. [0 hours] — source/calc: `F-A`
- **FACT** (high): Critical loads: emergency lighting and communications. — source/calc: `session://profile`
- **ASSUMPTION** (low) [A6]: The hazard sample puts the site in FEMA flood zone X with low flood risk. The sample is mock, stale, and labeled as a Queens site, so verify the zone for this lot before relying on it. If the zone is A, AE, AH, AO, V or VE, elevate the battery, inverters and switchgear.

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): Required before any rooftop work: a structural PE/RA analysis, a roof condition survey, a licensed electrician, FDNY rooftop access review, and Con Edison interconnection review. I cannot certify that the roof can hold the panels. — source/calc: `session://profile`
- **FACT** (medium): The city record shows no landmark flag, so no LPC review is triggered on that evidence. No parkland flag was returned. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`

## 11. Path to net-zero and learning resources

- **RECOMMENDATION** (low): Net-zero depends on the existing array. Since the array makes more kWh than your grid purchases, the open questions are timing of use and credits, not roof size alone. Once I know how the 457,000 kWh is used or credited, I can re-run the scenarios against the true baseline. — source/calc: `C3`
- **RECOMMENDATION** (low): No learning resources came from the tools in this run, so I list none. — source/calc: `session://profile`

## 12. Gaps, conflicts and confidence summary

- **FACT** (low): Main conflict: the financial tool assumes no existing solar. It treats a 316.7 kW whole-roof array as new, which gives a reduction above 100% and a Scenario C cost (about $2.7M-$4.2M) that does not fit your situation. Treat B and C solar results as low confidence. — source/calc: `F-C`
- **FACT** (high): intake_mismatch:floor_area_sqft: you entered 115,325 sq ft, the city record shows 135,600 sq ft. I kept yours. Please confirm. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): address_street_mismatch: the city lists 660 West 235 Street, you gave 660 West 236th Street. It may be another frontage of the same lot. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): missing_field:roof_replaced_year: roof age is unknown, so roof-related claims have lower confidence. — source/calc: `session://profile`
- **FACT** (medium): statewide_average_rate: the price is the New York commercial average, not your own tariff. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **FACT** (low): tariff_needs_user_confirmation: the tariff is a best match (Con Edison SC-9 Rate I, effective 2025-07-01). Please confirm it against a bill. — source/calc: `https://example.test/fictional/openei-tariff-v2`
- **FACT** (low): mock_data_in_live_run and stale_data: tariff, incentives, hazard and battery sizing come from saved sample data (retrieved 2025-10-01, over a year old), not live data. They are not facts about this site. Incentives are left out of net cost. — source/calc: `https://example.test/fictional/hazard-v0`
- **RECOMMENDATION** (medium): I assumed the 30% goal applies to the 226,605 kWh you buy from the grid. Please confirm. — source/calc: `session://profile`

## 13. Sources

- **FACT** (high): Your intake profile. — source/calc: `session://profile`
- **FACT** (high): NYC PLUTO building record, dataset pluto-26v2, retrieved 2026-10-15. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): PVWatts v8 solar output, retrieved 2026-10-15. — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **FACT** (medium): EIA retail electricity prices, through 2026-07, retrieved 2026-10-15. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **FACT** (low): Saved sample data (mock): tariff, incentives, hazard and battery sizing, retrieved 2025-10-01. — source/calc: `https://example.test/fictional/reopt-v0`

---
*All figures are planning-level estimates with ranges, not quotes or promises of savings. A licensed PE/RA must analyze the roof structure before any rooftop work. Send the existing array details and your bills, and I will re-run the comparison.*
