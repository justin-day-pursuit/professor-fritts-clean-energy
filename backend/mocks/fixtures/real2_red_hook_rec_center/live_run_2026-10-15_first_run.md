<!-- Live run on 2026-10-15: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools have no live version and answered from case 1's saved samples (so the hazard note says Queens). Status done; Check 4 passed on the first try. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **FACT** (high): Goal: cut grid electricity 30% by 2030 and keep critical loads (gym cooling, lighting, communications for a cooling center) running in outages, on a $750,000 capital budget (budget year 2027). — source/calc: `session://profile`
- **ESTIMATE** (medium): Scenario A (efficiency only) does not reach the 30% goal. It covers an estimated 10-20% of annual use and gives no backup power. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (standard efficiency plus a roof array capped at about 118.5 kW DC to fit the budget) reaches the goal on paper. It covers an estimated 47.8-61.6% of annual use, with upfront cost of $463,908-$750,000. It gives NO backup power in an outage, so it does not meet your resilience need. [47.8–61.6 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency, whole-roof 180 kW DC array, 960 kWh battery) reaches the goal and gives an estimated 6.8-8.0 hours of backup for the critical loads. Its estimated cost of $1,386,690-$2,203,104 is 1.85x to 2.94x your budget. It is over budget. [1,386,690–2,203,104 USD] — source/calc: `F-C`
- **RECOMMENDATION** (low): No scenario fits both goals inside $750,000. B meets the energy goal within budget but has no backup. C meets both but costs well over budget. A realistic path is B first with a battery for the critical loads added later when more funding is found, or a smaller critical-load battery sized by an engineer. Battery size and cost need a real design. — source/calc: `F-B`

## 2. Building profile and data provenance

- **FACT** (medium): Red Hook Recreation Center (NYC Parks), 155 Bay Street, Brooklyn; park recreation center built 1936; flat roof of 21,600 sq ft; Con Edison customer; annual use 375,066 kWh as entered. Roof replacement year was left blank (unknown). — source/calc: `session://profile`
- **FACT** (medium): Floor area mismatch: you entered 27,069 sq ft; the NYC PLUTO record shows 21,600 sq ft gross floor area (1 floor) and a lot of 212,400 sq ft. The lot size does not match your entered floor area. I kept your 27,069 sq ft as the working figure. Please confirm which is right. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): Address mismatch: the city record for the matched lot is 140 Lorraine Street, not 155 Bay Street. It may be another frontage of the same lot. The geocoder matched 155 Bay Street with a fallback match, so the building records may not be for this exact lot. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): The city record flags the lot as a landmark. Your profile context also shows it as parkland. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`

## 3. Assumptions register

- **ASSUMPTION** (medium) [A1]: A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ASSUMPTION** (medium) [A2]: A2: usable roof setback factor 0.55.
- **ASSUMPTION** (medium) [A3]: A3: array density of 66 sq ft per kW DC.
- **ASSUMPTION** (low) [A4]: A4: battery sizing is a fictional REopt stand-in sized for 8 hours of cooling-center backup (960 kWh, 120 kW). [960 kWh]
- **ASSUMPTION** (low) [A5]: A5: incentive programs and rules come from a mock sample fixture, pending live verification.
- **ASSUMPTION** (low) [A6]: A6: hazard ratings come from a mock sample fixture, pending site-specific assessment.
- **ASSUMPTION** (low) [A7]: A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model. [10–20 % of annual use]
- **ASSUMPTION** (low) [A9]: A9: planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open.

## 4. Baseline and efficiency opportunities

- **FACT** (medium): Baseline grid use is 375,066 kWh per year, as you entered. This is not checked against a bill in this run. [375,066 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (medium): A 30% cut is about 112,500 kWh per year at this baseline. [112,520 kWh/yr] — source/calc: `F-A`
- **ESTIMATE** (low): A standard efficiency package (LED and controls) is estimated to cut 37,507-75,013 kWh per year (10-20% of use) at an upfront cost of $108,276-$216,552. This is based on benchmarks (A7, A9), not a building model. [37,507–75,013 kWh/yr] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Do an ASHRAE-level energy audit of the 1936 building before choosing measures. Cooling, the cooling-center load, and envelope work are not covered by the benchmark. — source/calc: `F-A`

## 5. Solar assessment with calculations

- **ESTIMATE** (medium): Usable roof is about 11,880 sq ft (21,600 sq ft x 0.55 setback, A2). [11,880 sq ft] — source/calc: `C1`
- **ESTIMATE** (medium): Whole-roof array is about 180 kW DC (11,880 sq ft / 66 sq ft per kW, A3). [180 kW DC] — source/calc: `C2`
- **ESTIMATE** (medium): PVWatts estimates 215,488-236,764 kWh per year (central 226,143) for the 180 kW array. The range comes from the loss band in A1. [215,488–236,764 kWh/yr] — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **ESTIMATE** (low): Central solar output is about 60% of your annual use. This is much higher than the 15-25% typical for rooftop solar on a rec center, and the financial tool reports solar alone at 57.5-63.1% of use. That would mean solar alone passes the 30% goal on an annual-energy basis. Check it before relying on it. It depends on your 375,066 kWh figure and on the roof area being usable and structurally sound. It also assumes all output offsets grid purchases. [57.5–63.1 % of annual use] — source/calc: `C3`
- **ESTIMATE** (low): Annual solar savings are about $42,688-$57,250 per year. The low end uses the low kWh and low price; the high end uses the high kWh and high price. I did not run a central-case savings figure. [42,688–57,250 USD/yr] — source/calc: `C4`
- **FACT** (medium): Prices are the 12-month New York commercial average of $0.1981-$0.2418 per kWh, not this building's tariff. [0.1981–0.2418 USD/kWh] — source/calc: `https://www.eia.gov/electricity/data/browser/`

## 6. Scenario comparison table
*Simple payback with benchmark prices (A9), not the full SAM model. No incentives are counted in net cost. Battery sizing is sample data (A4).*

- **ESTIMATE** (medium): A, efficiency only: share of goal 33-67% (10-20% of use). Does NOT reach the 30% goal. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): A: upfront and net cost $108,276-$216,552 (no incentives counted). [108,276–216,552 USD] — source/calc: `F-A`
- **ESTIMATE** (low): A: simple payback 6.0-29.1 years. [6–29.1 years] — source/calc: `F-A`
- **ESTIMATE** (low): A: within budget (14-29% of $750,000). Outage hours: 0, no backup power. [14–29 % of budget] — source/calc: `F-A`
- **ESTIMATE** (low): B, efficiency + solar within budget (about 118.5 kW DC): reduction 47.8-61.6% of use, share of goal 159-205%. Reaches the goal by the tool's low-end test, but see the solar check in section 5. [47.8–61.6 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (low): B: upfront and net cost $463,908-$750,000 (no incentives counted). [463,908–750,000 USD] — source/calc: `F-B`
- **ESTIMATE** (low): B: simple payback 8.3-21.1 years. [8.3–21.1 years] — source/calc: `F-B`
- **ESTIMATE** (low): B: within budget but uses 62-100% of it, so the high-cost case leaves no contingency. Outage hours: 0, no backup power (panels shut off in an outage without a battery). [62–100 % of budget] — source/calc: `F-B`
- **ESTIMATE** (low): C, deep efficiency + 180 kW DC + 960 kWh battery: reduction 72.5-88.1% of use, share of goal 242-294%. Reaches the goal. [72.5–88.1 % of annual use] — source/calc: `F-C`
- **ESTIMATE** (low): C: upfront and net cost $1,386,690-$2,203,104 (no incentives counted). [1,386,690–2,203,104 USD] — source/calc: `F-C`
- **ESTIMATE** (low): C: simple payback 17.4-40.9 years. [17.4–40.9 years] — source/calc: `F-C`
- **ESTIMATE** (low): C: over budget (1.85x-2.94x of $750,000). Outage hours for the critical loads: 6.8-8.0. [6.8–8 hours] — source/calc: `F-C`

## 7. Cost, financing and incentives

- **ASSUMPTION** (low) [A9]: Costs use planning benchmarks (A9), not quotes. Get contractor quotes before committing capital.
- **ASSUMPTION** (low) [A5]: Left out of net cost: the federal commercial ITC (sample record shows 'open', placed-in-service deadline 2031-12-31 not confirmed; the sample record gives 2027-12-31) and a NYSERDA NY-Sun commercial incentive (sample record shows 'open'). Both come from saved sample data retrieved 2025-10-01, which is stale for a 7-day freshness window. Their status is uncertain, so neither is counted.
- **RECOMMENDATION** (low): Check with city counsel and NYC Parks how a public owner can claim federal credits (for example through elective pay), and check current status on the official NYSERDA and IRS pages before budgeting any incentive. — source/calc: `F-B`
- **ESTIMATE** (low): A $750,000 capital budget in 2027 covers scenario B at its low and high cost estimates ($463,908-$750,000) but not scenario C ($1,386,690-$2,203,104). [1,386,690–2,203,104 USD] — source/calc: `F-C`

## 8. Priority roadmap

- **RECOMMENDATION** (medium): Phase 0, confirm data and budget: pull 12-24 months of Con Edison bills, confirm the floor area (27,069 vs 21,600 sq ft) and address, confirm the tariff (SC-9 Rate I sample, effective 2025-07-01, unconfirmed), the roof replacement year, and whether the 2027 capital budget is firm. — source/calc: `session://profile`
- **RECOMMENDATION** (high): Phase 1, professional reviews: licensed structural PE/RA analysis and a roof condition survey. I cannot certify that the roof can hold panels. The roof age is unknown. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): Phase 2, efficiency measures: audit, then LED and controls and cooling upgrades, sized to the audit rather than the benchmark. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and interconnection: LPC review, parkland review by counsel, DOB electrical permit through a licensed electrician, FDNY rooftop access review, and the Con Edison interconnection application. — source/calc: `F-B`
- **RECOMMENDATION** (low): Phase 4, solar installation: install the array sized to the budget and to the structural result (scenario B is about 118.5 kW DC). — source/calc: `F-B`
- **RECOMMENDATION** (low): Phase 5, battery, commissioning and verification: add a critical-load battery when funded (scenario C sizing is 960 kWh, 120 kW), commission with an outage test, and check results against bills. — source/calc: `F-C`

## 9. Resilience and reliability plan

- **ESTIMATE** (low): Scenario C gives an estimated 6.8-8.0 hours of backup for the critical loads at about 120 kW (gym cooling, lighting and communications for a cooling center). The battery sizing is sample data (A4), not a design. [6.8–8 hours] — source/calc: `F-C`
- **ASSUMPTION** (low) [A4]: A4: battery sizing is a fictional REopt stand-in sized for 8 hours of cooling-center backup.
- **ESTIMATE** (medium): Scenarios A and B give no backup power. Solar panels shut off in an outage without a battery, so B alone does not keep the cooling center running. [0 hours] — source/calc: `F-B`
- **RECOMMENDATION** (medium): The center flooded in Hurricane Sandy, but the saved hazard sample lists flood zone X and low flood risk, and it describes a Queens site. I do not trust it for this building. Plan as if flood risk is real: put the battery, inverters and switchgear on the roof or above the design flood elevation, not in a ground-floor room. — source/calc: `F-C`
- **ASSUMPTION** (low) [A6]: The sample hazard record rates heat as moderate and winter storm as moderate. These are sample ratings (A6) and need a site-specific assessment.

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): Structural PE/RA analysis and a roof condition survey are mandatory. I cannot certify the roof; a licensed PE or RA must do the structural analysis. — source/calc: `session://profile`
- **RECOMMENDATION** (high): A licensed electrician, an FDNY rooftop access review, and a Con Edison interconnection review are required. — source/calc: `F-B`
- **RECOMMENDATION** (high): The lot is flagged as a landmark: get a Landmarks Preservation Commission (LPC) permit review before any rooftop or exterior work, since panels and equipment may be visible. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (high): The building is a park building: have counsel complete a parkland use review before installing solar. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): Flood-zone review under NYC Building Code Appendix G: the sample record says zone X, but the building flooded in Sandy. Confirm the zone on the official FEMA and NYC flood maps and complete the review if it is in a flood zone. — source/calc: `F-C`

## 11. Path to net-zero and learning resources

- **ESTIMATE** (low): At the central PVWatts output (about 60% of your use), a whole-roof array plus deep efficiency could cut grid purchases by an estimated 72.5-88.1% (scenario C). Reaching net-zero would need more than the roof can supply or off-site supply. [72.5–88.1 % of annual use] — source/calc: `F-C`
- **RECOMMENDATION** (low): No learning resource links were retrieved in this run, so none are listed. Ask NYC Parks energy staff and the Con Edison interconnection team for current guides. — source/calc: `F-C`

## 12. Gaps, conflicts and confidence summary

- **FACT** (medium): Intake mismatch on floor area: you entered 27,069 sq ft; the city record shows 21,600 sq ft (lot 212,400 sq ft, which does not match your number). I used 27,069 sq ft. Please confirm. Floor area only drives efficiency cost in the model. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): Address street mismatch: the city lot is 140 Lorraine Street; you gave 155 Bay Street. It may be another frontage of the same lot, and the address match was a fallback, so records may not be for this exact lot. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): Roof replacement year is missing. It is unknown, which lowers confidence in the roof's ability to carry panels and in the install timeline. — source/calc: `session://profile`
- **FACT** (medium): The electricity price is a New York statewide commercial average, not this building's tariff. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ASSUMPTION** (low) [A5]: The tariff (Con Edison SC-9 Rate I, effective 2025-07-01) is saved sample data, retrieved 2025-10-01, stale for a 90-day window, and needs your confirmation against a bill. Demand charges ($18-$24 per kW-month in the sample) are not modeled.
- **ASSUMPTION** (low) [A6]: Incentives (retrieved 2025-10-01, stale), hazard ratings and battery sizing are saved sample data (mock_data_in_live_run), not live. The hazard sample says Queens and flood zone X, which conflicts with Sandy flooding. Treated as unreliable.
- **ESTIMATE** (low): Solar output shows about 60% of your use, far above typical. The result depends on the 375,066 kWh entry, the 0.55 setback and the 66 sq ft per kW assumption, and has not been structurally checked. Scenario B and C results are low confidence for that reason. Annual-energy offset also does not show hour-by-hour use or export terms. [57.5–63.1 % of annual use] — source/calc: `C3`
- **RECOMMENDATION** (medium): No hidden-instruction pages, tool failures or blocked calls occurred in this run. No data was saved to the cache because nothing came from an approved official source in a form that could be saved. — source/calc: `F-A`

## 13. Sources
*Sample (mock) sources for tariff, incentives, hazard and battery are not cited as facts; see sections 3 and 12.*

- **FACT** (high): Your intake profile (session://profile). — source/calc: `session://profile`
- **FACT** (medium): NYC PLUTO building records (dataset pluto-26v2, retrieved 2026-10-15). — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): PVWatts v8 solar production (retrieved 2026-10-15, typical-year weather). — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **FACT** (medium): EIA electricity price data, New York commercial average (data through 2026-07, retrieved 2026-10-15). — source/calc: `https://www.eia.gov/electricity/data/browser/`

---
*Planning-level estimate only. All figures are ESTIMATE ranges from benchmark prices, not quotes. Nothing here guarantees savings or certifies the roof. A licensed PE or RA must do the structural analysis. Several inputs are saved sample data, listed in section 12.*
