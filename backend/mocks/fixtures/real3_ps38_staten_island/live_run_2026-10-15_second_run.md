<!-- Live run, second pass, 2026-10-15, after the roof/existing-systems/budget changes: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, footprints, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools answered from case 1's saved samples. Status done; Check 4 passed on the first try. Roof area is the footprint suggestion (34,360 sq ft). Tool calls: 16, 108.1 s. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **FACT** (high): Goal: cut grid electricity 30% by 2030 on a $600,000 capital budget (budget year 2027) at P.S. 38, 421 Lincoln Avenue, Staten Island. — source/calc: `session://profile`
- **ESTIMATE** (low): Scenario A (standard efficiency only) costs about $223,440-$446,880 and cuts about 10-20% of annual use. It fits the budget but does not reach the 30% goal (33-67% of the goal). [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (standard efficiency plus a 34 kW solar array sized to the budget) costs about $325,520-$600,000 and cuts about 24.1-35.5% of annual use. It fits the budget. It does not reliably reach the goal because the low end is below 30%; the high end is above it. [24.1–35.5 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency, whole-roof array of about 286 kW and a 960 kWh battery) reaches the goal, with a modeled reduction of 100% of annual use. It costs about $1,393,600-$2,542,260 more than your budget. Meeting the goal at full scale may take more than $600,000. Whether to extend the budget is your decision once you compare that gap with the savings. [1,393,600–2,542,260 USD over budget] — source/calc: `F-C`
- **RECOMMENDATION** (low): On the figures the tools returned, the most budget-realistic route is efficiency plus a budget-sized solar array (Scenario B). It may land near the 30% goal but is not certain to reach it. These are planning-level estimates, not quotes, and I cannot guarantee savings. — source/calc: `F-B`

## 2. Building profile and data provenance

- **FACT** (high): Entered by you: elementary school, 55,860 sq ft floor area, built 1955, flat roof of 34,360 sq ft, annual grid use 284,403 kWh, Con Edison, critical loads are emergency lighting and communications. Existing renewables: none. Existing efficiency work: none. So the plan assumes no existing systems and recommends no measure you already have. — source/calc: `session://profile`
- **FACT** (medium): The baseline for the goal is the electricity the building buys from the grid: 284,403 kWh per year, from the bills you entered. There is no existing solar to lower it. [284,403 kWh/yr] — source/calc: `session://profile`
- **FACT** (medium): The city record (PLUTO) lists gross floor area of 17,620 sq ft for this lot, which differs from the 55,860 sq ft you entered. The lot area is 65,000 sq ft, so the lot size does not match your floor area. I kept your 55,860 sq ft as the working figure. Please confirm it. Efficiency cost benchmarks scale with floor area, so efficiency costs would be lower if the city figure were correct. [17,620–55,860 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): City building footprints show 3 buildings on the lot totaling 34,363 sq ft of ground area, which is close to the 34,360 sq ft roof area you entered. A footprint is ground area, not a measured roof, and it may include buildings you do not intend to use. The roof area is your number, so have an engineer or roofer verify it. [34,363 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): Neither the profile nor the city record marks the building as a landmark. The record lists no parkland flag. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`

## 3. Assumptions register

- **ASSUMPTION** (medium) [A1]: ASSUMPTION A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ASSUMPTION** (medium) [A2]: ASSUMPTION A2: usable roof setback factor 0.55 (C1). — optional source/calc: `C1`
- **ASSUMPTION** (medium) [A3]: ASSUMPTION A3: array density of 66 sq ft per kW DC (C2). — optional source/calc: `C2`
- **ASSUMPTION** (low) [A4]: ASSUMPTION A4: sample battery size (fictional REopt stand-in sized for 8 hours of backup), not a site-specific design.
- **ASSUMPTION** (low) [A5]: ASSUMPTION A5: incentive programs and rules come from a mock sample fixture and are pending live verification.
- **ASSUMPTION** (low) [A6]: ASSUMPTION A6: hazard ratings come from a mock sample fixture and are pending site-specific assessment.
- **ASSUMPTION** (medium) [A7]: ASSUMPTION A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.
- **ASSUMPTION** (low) [A9]: ASSUMPTION A9: planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%. The 30% federal credit counts only when the incentives tool says the program is open.

## 4. Baseline and efficiency opportunities

- **FACT** (medium): Baseline grid use is 284,403 kWh per year. The bills are in the intake, so no benchmark use was needed. [284,403 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (low): Standard efficiency (for example LED lighting and controls) is estimated to cut 28,440-56,881 kWh per year, which is 10-20% of use, at a cost of about $223,440-$446,880. Because the building has no efficiency work done, no benchmark savings are reduced for existing work. There is no building model, so confidence is low. [28,440–56,881 kWh/yr] — source/calc: `F-A`
- **ASSUMPTION** (medium) [A7]: Efficiency savings of 10-20% of annual use are a published benchmark, not a model of this school.
- **RECOMMENDATION** (medium): Get an investment-grade energy audit to replace the benchmark with measured savings, and check the 55,860 sq ft floor area first. The cost benchmarks depend on it. — source/calc: `F-A`

## 5. Solar assessment with calculations

- **ESTIMATE** (medium): Usable roof area is about 18,898 sq ft (34,360 sq ft times the 0.55 setback factor). [18,898 sq ft] — source/calc: `C1`
- **ESTIMATE** (medium): Array size that fits the usable roof is about 286 kW DC (at 66 sq ft per kW). [286.3 kW DC] — source/calc: `C2`
- **ESTIMATE** (medium): PVWatts estimates the whole-roof array produces about 338,147-371,605 kWh per year (central about 354,876 kWh). The model used a 10-degree tilt facing south on a flat roof. [338,147–371,605 kWh/yr] — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **ASSUMPTION** (medium) [A1]: The solar range comes from the loss band: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ESTIMATE** (low): The gross value of the whole-roof production at the EIA statewide commercial price is about $66,987-$89,854 per year (central about $78,783). This values all production, including surplus. The scenario savings in section 6 credit only the solar that replaces power the building still uses. [66,987–89,854 USD/yr] — source/calc: `C4`
- **ESTIMATE** (low): The roof could produce more than the building uses: whole-roof solar alone is about 118.9-130.7% of annual use. The surplus is potential that flows to the grid. It is not counted in the savings because export credits depend on net-metering rules that were not checked. [118.9–130.7 % of annual use] — source/calc: `F-C`
- **FACT** (medium): Electricity price: the EIA New York commercial 12-month average is about $0.2220 per kWh (range $0.1981-$0.2418) as of July 2026. This is a statewide average, not this building's own tariff. [0.1981–0.2418 USD/kWh] — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **RECOMMENDATION** (medium): Have an engineer or roofer verify the roof area, the usable area after setbacks, shading and structure before any design. Roof area is your number and is not verified. — source/calc: `C1`

## 6. Scenario comparison table

- **ESTIMATE** (low): Scenario A (efficiency only): reduction 10-20% of annual use, 33-67% of the goal. Upfront cost about $223,440-$446,880. Net cost the same (no incentives counted). Simple payback about 16.2-79.3 years. Budget strain: within budget (37-74% of budget). Outage backup: 0 hours. Does not reach the goal. [223,440–446,880 USD upfront] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (efficiency plus 34 kW solar within budget): reduction 24.1-35.5% of annual use, 80-118% of the goal. Upfront and net cost about $325,520-$600,000. Annual savings about $13,594-$24,432. Simple payback about 13.3-44.1 years. Budget strain: within budget (54-100% of budget). Outage backup: 0 hours. It does not reach the goal at the low end, so it is not certain to reach it. [325,520–600,000 USD upfront] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency, about 286 kW solar, 960 kWh battery): reduction 100% of annual use (capped at the building's use), 333% of the goal. Upfront and net cost about $1,993,600-$3,142,260. Annual savings about $56,340-$68,769. Simple payback about 29.0-55.8 years. Budget strain: over budget (3.3-5.2 times the budget). Outage backup about 6.8-8.0 hours. It reaches the goal. It costs $1,393,600-$2,542,260 more than your budget, so meeting the goal at this scale may take more than the $600,000 set aside. [1,993,600–3,142,260 USD upfront] — source/calc: `F-C`
- **ESTIMATE** (low): Solar surplus in Scenario C is about 96,405-158,303 kWh per year. It is potential that flows to the grid and is not counted in the savings or payback, because net-metering and export-credit rules were not checked. No reduction above 100% is claimed. [96,405–158,303 kWh/yr] — source/calc: `F-C`
- **ESTIMATE** (low): Rooftop solar alone could in principle cover more than the building's annual use (about 119-131%). It still needs the efficiency work and the budget to build, and the whole-roof array does not fit the $600,000 budget. Scenario A without solar does not reach the goal. — source/calc: `F-A`
- **ASSUMPTION** (low) [A9]: Paybacks are a simple payback (cost divided by annual savings), not the full SAM model. The wide ranges come from benchmark prices and savings percentages.

## 7. Cost, financing and incentives

- **ASSUMPTION** (low) [A5]: No incentive is counted in any net-cost figure. The incentive tool returned mock sample data retrieved 2025-10-01, which is stale. It lists a federal commercial ITC (placed-in-service deadline 2027-12-31) and a NY-Sun commercial incentive as open. These programs are uncertain and are left out of net cost. They may not apply to a public school, so confirm eligibility on the official program pages.
- **ESTIMATE** (low): Scenario A and Scenario B fit the $600,000 capital budget. Scenario C costs $1,393,600-$2,542,260 more than your budget and reaches the goal. Meeting the goal may take more than the budget. Whether to extend it is your decision once you compare that gap with the savings. [1,393,600–2,542,260 USD over budget] — source/calc: `F-C`
- **ASSUMPTION** (low) [A9]: Costs use planning-level benchmark prices, not quotes. Get contractor quotes before committing the 2027 capital budget.
- **RECOMMENDATION** (low): Because the incentive data is stale and mock, check the current status of the federal credit and NY-Sun on the official pages. Re-run the scenarios if a program is open to public schools. Any favorable change should be counted only after it is confirmed. — source/calc: `F-B`

## 8. Priority roadmap

- **RECOMMENDATION** (medium): Phase 0, confirm data and budget: confirm the floor area (55,860 vs 17,620 sq ft), roof area, 12 months of bills, budget year and type (2027 capital), the roof replacement year, and the actual Con Edison tariff. — source/calc: `F-A`
- **RECOMMENDATION** (high): Phase 1, professional reviews: have a licensed structural PE/RA analyze the roof and complete a roof condition survey before design. I cannot certify that the roof can hold panels. — source/calc: `C1`
- **RECOMMENDATION** (medium): Phase 2, efficiency measures: install the standard efficiency package (LED lighting and controls) first, since it lowers the load that solar must cover. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and interconnection: engage a licensed electrician, obtain NYC permits, arrange FDNY rooftop access and file the Con Edison interconnection application. — source/calc: `F-B`
- **RECOMMENDATION** (low): Phase 4, solar installation: install the budget-sized array (about 34 kW in Scenario B), leaving room to add more roof capacity later if funding allows. — source/calc: `F-B`
- **RECOMMENDATION** (low): Phase 5, battery, commissioning and verification: add a battery if funding is extended, commission the system and compare metered results with bills against the 2030 goal. — source/calc: `F-C`

## 9. Resilience and reliability plan

- **ESTIMATE** (low): Scenario C's battery would carry the critical loads (emergency lighting and communications) for about 6.8-8.0 hours in an outage. [6.8–8 hours] — source/calc: `F-C`
- **ESTIMATE** (medium): Scenarios A and B give no backup power. Solar panels shut off in an outage without a battery. [0 hours] — source/calc: `F-B`
- **ASSUMPTION** (low) [A4]: ASSUMPTION A4: the battery is a sample size (960 kWh, 120 kW) from a fictional stand-in sized for 8 hours of cooling-center backup, not for this school's emergency lighting and communications. It likely oversizes the battery for those loads and should be re-sized.
- **ASSUMPTION** (low) [A6]: The hazard sample shows flood zone X, low flood rating, moderate heat and moderate winter storm. It is mock data (A6) and notes a Queens site, so it may not describe this lot. No flood-zone review is triggered by zone X, but confirm the zone against official FEMA/NYC flood maps.

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): Structural analysis by a licensed PE or RA is required before solar. I cannot certify the roof can hold the panels. — source/calc: `C1`
- **RECOMMENDATION** (high): A roof condition survey is required. The roof replacement year is missing from the intake, and the roof's remaining life affects the panel installation. — source/calc: `C1`
- **RECOMMENDATION** (high): A licensed electrician must design and install the system. FDNY rooftop access and setback review is required. — source/calc: `F-B`
- **RECOMMENDATION** (high): A Con Edison utility interconnection review and application is required. Check net-metering and export rules before counting any surplus. — source/calc: `F-C`
- **RECOMMENDATION** (medium): Verify the roof area and the floor area with an engineer or roofer and the city record. — source/calc: `C1`

## 11. Path to net-zero and learning resources

- **ESTIMATE** (low): On paper, the full roof could produce more than the building's annual grid use (about 119-131%). Deep efficiency plus the whole-roof array is the route to net-zero grid electricity (Scenario C). It needs roughly $2.0-3.1 million at benchmark prices, versus a $600,000 budget, so it may be a multi-year, multi-source plan. — source/calc: `F-C`
- **RECOMMENDATION** (low): A staged route: efficiency now, a budget-sized array (Scenario B), then expand the array and add a battery as later capital or grants allow. Treat each stage as a new planning run with quotes. — source/calc: `F-B`

## 12. Gaps, conflicts and confidence summary

- **FACT** (medium): Flag intake_mismatch:floor_area_sqft: you entered 55,860 sq ft and the city record shows 17,620 sq ft gross floor area. The lot is 65,000 sq ft. I kept your value, and ask you to confirm it. Efficiency costs and savings carry low confidence until then. [17,620–55,860 sq ft] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (medium): Flag missing_field:roof_replaced_year: the roof age is unknown, so the roof condition and remaining life are unknown. Solar confidence is lowered. Please provide it. — source/calc: `C1`
- **FACT** (medium): Flag statewide_average_rate: the price is the New York commercial average, not this building's own tariff. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **RECOMMENDATION** (low): Flags tariff_needs_user_confirmation, mock_data_in_live_run and stale_data: the tariff returned is sample data, SC-9 Rate I (General Large), effective 2025-07-01, retrieved 2025-10-01, with energy $0.20-$0.24 per kWh. It is not confirmed against a bill. Please confirm your actual tariff. — source/calc: `https://example.test/fictional/openei-tariff-v2`
- **ASSUMPTION** (low) [A5]: Flags mock_data_in_live_run and stale_data: the incentive (A5), hazard (A6) and battery (A4) results are saved sample data retrieved 2025-10-01, so they are not facts. Confidence is low and no incentive is counted.
- **RECOMMENDATION** (medium): The roof area you entered is close to the city's footprint total, but a footprint is ground area, not a measured roof. Have it verified. — source/calc: `C1`
- **ESTIMATE** (low): Net-metering and export credit rules were not checked, so the solar surplus is not credited. Payback figures are simple paybacks and not the full SAM model. — source/calc: `F-C`
- **RECOMMENDATION** (medium): I cannot guarantee savings. Every figure is an estimate with a range. I did not save any data to the reference cache, because none of it came from a verified official page. — source/calc: `F-B`

## 13. Sources

- **FACT** (high): Your intake profile (entered by you). — source/calc: `session://profile`
- **FACT** (medium): NYC PLUTO tax lot data, dataset pluto-26v2, retrieved 2026-10-15. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): PVWatts v8 solar production, retrieved 2026-10-15. — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **FACT** (medium): EIA electricity retail price data (July 2026), retrieved 2026-10-15. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ESTIMATE** (low): Scenario results come from the planning-level financial model (F-A, F-B, F-C). Tariff, incentive, hazard and battery data are saved sample data and are not sources of fact. — source/calc: `F-A`

---
*Planning-level estimates only, not quotes or guarantees. A licensed PE or RA must do the structural analysis before any solar work.*
