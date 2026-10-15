<!-- Live run, second pass, 2026-10-15, after the roof/existing-systems/budget changes: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, footprints, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools answered from case 1's saved samples. Status done; Check 4 passed on the first try. The existing-systems section was left blank, and the plan asks once. Tool calls: 17, 129.1 s. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **ESTIMATE** (medium): Scenario B (standard efficiency plus a 118.5 kW solar array) is estimated to cut grid purchases by about 47.8-61.6% of annual use, above the 30% goal. Its estimated cost is $463,908-$750,000, which fits the $750,000 budget (the high end uses all of it). It gives no backup power in an outage. [47.8–61.6 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (medium): Scenario A (efficiency only) is estimated to cut 10-20% of annual use. It does not reach the 30% goal on its own. It costs $108,276-$216,552. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario C (deep efficiency, whole-roof solar and a 960 kWh battery) reaches the goal and gives 6.8-8.0 hours of critical-load backup. It costs $1,668,190-$2,625,354. That is $918,190-$1,875,354 more than your $750,000 budget. [1,668,190–2,625,354 USD] — source/calc: `F-C`
- **RECOMMENDATION** (medium): Meeting both the 30% goal and outage backup for the cooling center may take more than $750,000. Whether to extend the budget is your decision, after you compare the gap with the savings. I can't guarantee savings. Every figure here is an estimate range based on planning-level benchmark prices. — source/calc: `F-C`
- **ASSUMPTION** (medium) [A9]: Planning-level benchmark prices, not quotes, sit behind all three scenarios.

## 2. Building profile and data provenance

- **FACT** (high): You entered: Red Hook Recreation Center (NYC Parks), 155 Bay Street, Brooklyn; built 1936; flat roof; 27,069 sq ft floor area; 32,860 sq ft roof area; Con Edison customer; 2027 capital budget of $750,000. [27,069 sq ft floor area] — source/calc: `session://profile`
- **FACT** (high): The baseline for the goal is the electricity the building buys from the grid: 375,066 kWh per year, from the intake. [375,066 kWh/yr] — source/calc: `session://profile`
- **FACT** (medium): The city record (PLUTO) lists 21,600 sq ft gross floor area, but you entered 27,069 sq ft. I kept your 27,069 sq ft as the working figure. Please confirm which is right. The lot is 212,400 sq ft, which does not match your floor area. [21,600–27,069 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): The city's address for this lot is 140 Lorraine Street, while you gave 155 Bay Street. It may be another frontage of the same lot. The geocoder matched 155 Bay Street to this lot (tax lot 3005820001). — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): City building footprints show 4 buildings on the lot totaling 32,862 sq ft (27,000; 4,370; 825; 667). That is close to your 32,860 sq ft roof area, but a footprint is ground area, not a measured roof, and the lot holds more than one building. I used your roof area; please confirm it with an engineer or roofer. [32,860–32,862 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): The city record flags this site as a landmark, and the site is NYC Parks parkland. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (medium): You did not list existing solar, other renewables or efficiency work already done. The plan assumes there are none. Please tell me if any exist already (for example LED lighting), because that would lower the savings and the roof area available. — source/calc: `session://profile`

## 3. Assumptions register

- **ASSUMPTION** (medium) [A1]: A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ASSUMPTION** (medium) [A2]: A2: usable roof setback factor 0.55 (C1). — optional source/calc: `C1`
- **ASSUMPTION** (medium) [A3]: A3: array density factor 66 sq ft per kW DC (C2). — optional source/calc: `C2`
- **ASSUMPTION** (low) [A4]: A4: battery sizing comes from a fictional REopt stand-in sized for 8 hours of cooling-center backup (saved sample data).
- **ASSUMPTION** (low) [A5]: A5: incentive programs and rules come from a mock sample fixture, pending live verification.
- **ASSUMPTION** (low) [A6]: A6: hazard ratings come from a mock sample fixture, pending a site-specific assessment.
- **ASSUMPTION** (medium) [A7]: A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.
- **ASSUMPTION** (medium) [A9]: Planning-level benchmark prices, not quotes, sit behind all three scenarios.

## 4. Baseline and efficiency opportunities

- **FACT** (high): Grid electricity bought today is 375,066 kWh per year. The 30% goal is about 112,520 kWh per year. [375,066 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (low): A standard efficiency package (LED and controls) is estimated to save 37,507-75,013 kWh per year (10-20% of use). It costs $108,276-$216,552 and saves about $7,430-$18,138 per year. This is a benchmark, not a building model. [37,507–75,013 kWh/yr] — source/calc: `F-A`
- **ASSUMPTION** (low) [A7]: The efficiency savings benchmark is 10-20% of annual use. I did not use a building model.
- **RECOMMENDATION** (medium): Start with LED lighting and controls, then have an energy auditor review cooling for the gym, which is a critical load. Efficiency work already done would lower these savings. I assumed none. — source/calc: `F-A`

## 5. Solar assessment with calculations

- **ESTIMATE** (medium): Usable roof for solar is about 18,073 sq ft, from your 32,860 sq ft roof with a 0.55 setback factor. [18,073 sq ft] — source/calc: `C1`
- **ESTIMATE** (medium): The whole usable roof fits an array of about 273.8 kW DC, at 66 sq ft per kW. [273.8 kW DC] — source/calc: `C2`
- **ESTIMATE** (medium): Annual solar output for that array is estimated at 327,822-360,189 kWh (central 344,031 kWh). The range comes from the loss band in A1. PVWatts assumed a flat roof at 10 degree tilt facing south. [327,822–360,189 kWh/yr] — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **ESTIMATE** (medium): The central output is about 0.92 of annual use. [0.9173 fraction of annual use] — source/calc: `C3`
- **ESTIMATE** (low): Whole-roof solar alone is modeled at about 87-96% of annual use. That is far above the 15-25% typical for rooftop solar, because this roof is large compared with 375,066 kWh of use. Please confirm the roof area and structure before relying on it. Solar alone also gives no backup power in an outage. [87.4–96 % of annual use] — source/calc: `F-C`
- **ESTIMATE** (medium): Gross solar savings are estimated at $64,941-$87,094 per year (central $76,375). They use the EIA New York commercial average price of $0.1981-$0.2418 per kWh (central $0.222), not this building's own tariff. [64,941–87,094 USD/yr] — source/calc: `C4`
- **ESTIMATE** (low): Under Scenario C the roof could make 9,015-78,889 kWh per year more than the building uses. That surplus is not counted in the savings, because export credits depend on net-metering rules I did not check. [9,015–78,889 kWh/yr] — source/calc: `F-C`

## 6. Scenario comparison table

- **ESTIMATE** (medium): Scenario A (efficiency only): reduction of 10-20% of annual use, which is 33-67% of the goal. It does not reach the 30% goal. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario A: upfront and net cost $108,276-$216,552 (no incentives counted). Simple payback is 6.0-29.1 years. Budget strain is low (14-29% of budget). Outage backup is 0 hours. [108,276–216,552 USD] — source/calc: `F-A`
- **ESTIMATE** (medium): Scenario B (standard efficiency plus 118.5 kW solar, capped to fit the budget): reduction of 47.8-61.6% of annual use, which is 159-205% of the goal. It reaches the goal. [47.8–61.6 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario B: upfront and net cost $463,908-$750,000 (no incentives counted). Savings are about $35,544-$55,842 per year, and simple payback is 8.3-21.1 years. Budget use is 62-100%, so the high end leaves no contingency. Outage backup is 0 hours. [463,908–750,000 USD] — source/calc: `F-B`
- **ESTIMATE** (medium): Scenario C (deep efficiency, 273.8 kW solar, 960 kWh battery): reduction is capped at 100% of annual use, which is 333% of the goal. It reaches the goal. [100 % of annual use] — source/calc: `F-C`
- **ESTIMATE** (low): Scenario C: upfront and net cost $1,668,190-$2,625,354 (no incentives counted). Savings are about $74,301-$90,691 per year, and simple payback is 18.4-35.3 years. Outage backup is 6.8-8.0 hours. The tool says it reaches the goal but costs $918,190-$1,875,354 more than your budget. Reaching the goal may take more than the amount set aside; compare that gap with the savings before deciding whether to extend it. [918,190–1,875,354 USD over budget] — source/calc: `F-C`
- **ASSUMPTION** (medium) [A9]: Payback figures are a simple payback, not the full SAM model. All cost figures are planning-level ranges, not quotes.

## 7. Cost, financing and incentives

- **ESTIMATE** (low): Net cost equals upfront cost in every scenario because no incentive is counted: A $108,276-$216,552; B $463,908-$750,000; C $1,668,190-$2,625,354. [463,908–750,000 USD] — source/calc: `F-B`
- **ASSUMPTION** (low) [A5]: Left out of net cost: the Federal commercial ITC (sample data lists it as open with a 2027-12-31 placed-in-service deadline) and a NYSERDA NY-Sun commercial incentive. Both come from saved sample data retrieved 2025-10-01, so they are stale and uncertain. They are not counted until checked on the official pages.
- **ESTIMATE** (low): The budget is a 2027 capital budget of $750,000. Scenario B fits it, but B has no battery. Scenario C adds backup but costs $918,190-$1,875,354 more than your budget. Whether to extend the budget is your decision. [918,190–1,875,354 USD over budget] — source/calc: `F-C`
- **RECOMMENDATION** (medium): Ask for contractor quotes for B and for a middle option that adds a smaller battery to B. I have not costed that option. Also ask NYC Parks capital staff whether other city, state or federal funds are open. I confirmed none from official pages. — source/calc: `F-B`

## 8. Priority roadmap

- **RECOMMENDATION** (medium): Phase 0, confirm data and budget: collect 12 months of Con Edison bills, confirm the 2027 capital budget, confirm the tariff (sample shows SC-9 Rate I, effective 2025-07-01), and confirm floor area, roof area and any existing systems. — source/calc: `session://profile`
- **RECOMMENDATION** (high): Phase 1, professional reviews: a structural PE/RA analysis of the roof and a roof condition survey (the roof replacement year is unknown). Also have an engineer or roofer verify the usable roof area. I cannot certify that the roof can hold the panels. — source/calc: `C1`
- **RECOMMENDATION** (medium): Phase 2, efficiency measures: LED lighting, controls and a cooling review, estimated to save 10-20% of annual use. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and interconnection: Con Edison interconnection application, a licensed electrician, FDNY rooftop access review, and the LPC advisory report and parkland review in section 10. — source/calc: `F-B`
- **RECOMMENDATION** (medium): Phase 4, solar installation: start with the budget-capped 118.5 kW array (Scenario B), or the whole roof if the budget is extended, after the structural review. — source/calc: `F-B`
- **RECOMMENDATION** (medium): Phase 5, battery, commissioning and verification: add a battery with a critical-load panel, placed above flood level. Commission, then check results against 12 months of bills. — source/calc: `F-C`

## 9. Resilience and reliability plan

- **ESTIMATE** (low): Scenario C's battery (960 kWh, 120 kW) is estimated to carry critical loads for 6.8-8.0 hours. The battery size is sample data. [6.8–8 hours] — source/calc: `F-C`
- **ASSUMPTION** (low) [A4]: Battery sizing is a fictional REopt stand-in sized for 8 hours of cooling-center backup.
- **ESTIMATE** (medium): Scenarios A and B give no backup power (0 hours). Solar panels shut off in an outage without a battery. [0 hours] — source/calc: `F-B`
- **FACT** (high): Critical loads: gym cooling, lighting and communications for the cooling center. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): You say the center flooded in Hurricane Sandy. The sample hazard data shows flood zone X and low flood rating, but it is marked for a Queens site and is stale, so I did not rely on it. Put the battery, inverters and switchgear on the roof or above the design flood elevation. — source/calc: `F-C`
- **RECOMMENDATION** (medium): Confirm with NYC Parks how many hours or days of cooling-center operation are required. About 8 hours may not cover a multi-day outage, and longer backup would cost more. — source/calc: `F-C`

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): A licensed PE or RA must do the structural analysis. A roof condition survey is also required. I cannot certify the roof. — source/calc: `C1`
- **RECOMMENDATION** (high): A licensed electrician, FDNY rooftop access review and a Con Edison interconnection review are required. — source/calc: `F-B`
- **RECOMMENDATION** (medium): The site is flagged as a landmark and is on parkland. The Landmarks Preservation Commission gives the owning agency an advisory report, not a permit, so request that review before rooftop or exterior work. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (medium): Counsel should do a parkland use review before any solar or battery work. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (medium): Do a flood-zone review (NYC Building Code Appendix G) against the official flood maps. The center flooded in Sandy, and the sample data that says zone X is unreliable. — source/calc: `F-C`

## 11. Path to net-zero and learning resources

- **ESTIMATE** (low): Scenario C is modeled as cutting 100% of grid purchases. This depends on a verified roof, deep efficiency, and the surplus not being counted. This is a path toward net-zero electricity, not proof of it. [100 % of annual use] — source/calc: `F-C`
- **RECOMMENDATION** (medium): Phase the work: efficiency first, then budget-capped solar, then battery and the rest of the roof as funds allow. Before 2030, ask Con Edison and NYC Parks about export and net-metering rules for surplus power. I have not checked them and found no learning resources from my tools. — source/calc: `F-C`

## 12. Gaps, conflicts and confidence summary

- **RECOMMENDATION** (medium): Missing from the intake: the roof replacement year and existing systems. The plan assumes no existing solar or efficiency work. Please confirm. — source/calc: `session://profile`
- **FACT** (medium): Floor area conflict: you entered 27,069 sq ft and the city record shows 21,600 sq ft. I used 27,069. The efficiency cost and savings depend on it, so confidence is lowered. The city address (140 Lorraine Street) also differs from yours (155 Bay Street). [21,600–27,069 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): Electricity price is the New York commercial statewide average, not this building's tariff. It covers the 12 months to 2026-07. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **RECOMMENDATION** (low): Tariff: the sample shows Con Edison SC-9 Rate I (General Large), effective 2025-07-01. It is mock data retrieved 2025-10-01 and stale (over a year old; the limit is 90 days). Please confirm the tariff against a bill. — source/calc: `https://example.test/fictional/openei-tariff-v2`
- **ASSUMPTION** (low) [A5]: Incentive data is saved sample data from 2025-10-01, past the 7-day limit. It was not refreshed or saved to the cache, and is left out of net cost.
- **ASSUMPTION** (low) [A6]: Hazard data is saved sample data from 2025-10-01, labeled for a Queens site. It shows flood zone X, which conflicts with your Sandy flooding. I kept the cautious flood plan.
- **ASSUMPTION** (low) [A4]: Battery sizing and outage hours come from sample data and are low confidence.
- **ESTIMATE** (low): The modeled solar share of use (87-96%) is far above typical, and the roof area may span four buildings. Confidence in solar-based results is medium to low until an engineer verifies the roof area. [87.4–96 % of annual use] — source/calc: `F-C`

## 13. Sources

- **FACT** (medium): NYC PLUTO tax lot data (building records and footprints), retrieved 2026-10-15. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): PVWatts v8 solar production, retrieved 2026-10-15. — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **FACT** (medium): EIA electricity retail price data, retrieved 2026-10-15. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **FACT** (high): Intake profile entered by you. — source/calc: `session://profile`
- **ASSUMPTION** (low) [A5]: Sample (mock) data for incentives, hazard and battery sizing: not official sources. — optional source/calc: `https://example.test/fictional/incentives-v0`

---
*Planning-level estimates only. This is not a structural, electrical or financial certification. A licensed PE or RA must review the roof before any solar work.*
