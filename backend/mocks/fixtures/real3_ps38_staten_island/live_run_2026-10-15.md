<!-- Live run on 2026-10-15: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools have no live version and answered from case 1's saved samples (so the hazard note says Queens). Status done; Check 4 passed on the first try. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **FACT** (high): Goal: cut grid electricity 30% by 2030 at P.S. 38 (R038), 421 Lincoln Avenue, Staten Island, on a $600,000 capital budget (budget year 2027). — source/calc: `session://profile`
- **ESTIMATE** (medium): Efficiency only (Scenario A) is estimated to cut 10-20% of annual use, which is 33-67% of the 30% goal. It does not reliably reach the goal on its own. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Efficiency plus a budget-capped solar array (Scenario B, about 34 kW DC) is estimated to cut 24-36% of annual use. The model's goal test uses the low end, so it reports 'does not reach'. The high end passes 30%. This is the best fit for the $600k budget, but the high-cost case uses the whole budget. [24.1–35.5 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (low): The full path (Scenario C: deep efficiency, whole-roof array, 960 kWh battery) clears the goal on paper. It costs an estimated $2.5M-$3.9M, which is 4.2-6.5 times the budget, so it is over budget. [2,509,600–3,916,260 USD] — source/calc: `F-C`
- **RECOMMENDATION** (medium): Recommendation: pursue Scenario B. Do efficiency first, then add solar sized to what is left of the budget after quotes. First confirm the floor area and roof area (see sections 2 and 12), because they drive every cost and solar figure. — source/calc: `F-B`

## 2. Building profile and data provenance

- **FACT** (high): You entered: elementary school, built 1955, flat roof, 55,000 sq ft roof, 55,860 sq ft floor area, annual grid use 284,403 kWh, Con Edison, critical loads are emergency lighting and communications. The roof replacement year was left blank (missing_field:roof_replaced_year). — source/calc: `session://profile`
- **FACT** (medium): The NYC PLUTO record for this lot (BBL 5037320006) lists gross floor area of 17,620 sq ft, one floor, lot area 65,000 sq ft, building class W1, and no landmark flag. This differs from the 55,860 sq ft you entered (intake_mismatch:floor_area_sqft). The lot size does not match your floor area. I kept your 55,860 sq ft as the working figure; please confirm which is correct. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (medium): If the city's 17,620 sq ft one-story figure is right, a 55,000 sq ft roof is not plausible. In that case the array size, solar output and savings below are overstated. Please confirm the roof area from drawings or a survey. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`

## 3. Assumptions register

- **ASSUMPTION** (medium) [A1]: A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ASSUMPTION** (medium) [A2]: A2: usable roof setback factor 0.55 (applied in C1). — optional source/calc: `C1`
- **ASSUMPTION** (medium) [A3]: A3: array density of 66 sq ft per kW DC (applied in C2). — optional source/calc: `C2`
- **ASSUMPTION** (low) [A4]: A4: fictional REopt stand-in battery sizing for 8 hours of cooling-center backup (saved sample data, mock).
- **ASSUMPTION** (low) [A5]: A5: incentive programs and rules come from a saved mock sample, pending live verification.
- **ASSUMPTION** (low) [A6]: A6: hazard ratings come from a saved mock sample, pending a site-specific assessment.
- **ASSUMPTION** (medium) [A7]: A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.
- **ASSUMPTION** (medium) [A9]: A9: planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open.

## 4. Baseline and efficiency opportunities

- **FACT** (medium): Baseline: 284,403 kWh per year of grid use, from your intake. This is a measured-style figure, so no benchmark use was needed. Per sq ft it is about 5.1 kWh on your floor area, or about 16 kWh on the city's floor area. This is another reason to confirm the floor area. [284,403 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (medium): A standard efficiency package (LED and controls) is estimated to save 10-20% of annual use, or 28,440-56,881 kWh/yr. Standard efficiency is benchmarked at $4-8 per sq ft, which is $223,440-$446,880 on your floor area. [28,440–56,881 kWh/yr] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Efficiency is not a building-model result. An ASHRAE Level 2 energy audit would replace the benchmark with measured opportunities. — source/calc: `F-A`

## 5. Solar assessment with calculations

- **ESTIMATE** (low): Usable roof is about 30,250 sq ft after setbacks, based on the 55,000 sq ft roof you entered. [30,250 sq ft] — source/calc: `C1`
- **ESTIMATE** (low): Whole-roof array is about 458 kW DC. [458.3 kW DC] — source/calc: `C2`
- **ESTIMATE** (medium): PVWatts estimates 541,272-594,828 kWh/yr AC for that array, central value 568,050 kWh/yr. The range comes from the loss band in A1. [541,272–594,828 kWh/yr] — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **ESTIMATE** (low): On paper the whole-roof array would produce about 2.0 times the school's annual use (C3 central 1.997; the model gives 190-209% of use). This is much higher than the usual 15-25% for school roofs. It follows from the large roof area entered and the modest annual use. It likely overstates what is real if the roof area is wrong, and it assumes exported power earns retail value. [1.997 fraction of annual use] — source/calc: `C3`
- **ESTIMATE** (low): Gross annual solar value for the whole-roof array is $107,226-$143,829 per year, central $126,107. These use the low kWh with the low price, the high kWh with the high price, and the 12-month average price. [107,226–143,829 USD/yr] — source/calc: `C4`
- **FACT** (medium): The price used is the EIA New York commercial average of $0.1981-$0.2418 per kWh, central $0.222. It is not this building's own tariff (statewide_average_rate). [0.1981–0.2418 USD/kWh] — source/calc: `https://www.eia.gov/electricity/data/browser/`

## 6. Scenario comparison table

- **ESTIMATE** (medium): Scenario A (efficiency only, no solar): reduction is 10.0-20.0% of annual use, 33-67% of the 30% goal. It does not reach the goal (reaches_goal false). [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (medium): Scenario A cost: upfront and net cost $223,440-$446,880 (no incentives counted). Annual savings $5,634-$13,754. Simple payback 16.2-79.3 years. Budget strain: within budget (37-74% of budget). Backup outage hours: 0. Simple payback, not the full SAM model. [223,440–446,880 USD] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (efficiency plus about 34 kW DC solar capped to the budget): reduction is 24.1-35.5% of annual use, 80-118% of the goal. The model reports reaches_goal false because the low end is under 30%. The high end is above it. [24.1–35.5 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario B cost: upfront and net cost $325,520-$600,000 (no incentives counted). Annual savings $13,594-$24,432. Simple payback 13.3-44.1 years. Budget strain: within budget (54-100% of budget; the high end leaves no contingency). Backup outage hours: 0. Simple payback, not the full SAM model. [325,520–600,000 USD] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency, 458 kW DC whole-roof array, 960 kWh battery): the model shows a 205-234% reduction of annual use (net of the whole-roof output) and reaches the goal (reaches_goal true). That figure depends on the roof area and on exports being valued at retail, so treat it as an upper bound. [205.3–234.1 % of annual use] — source/calc: `F-C`
- **ESTIMATE** (low): Scenario C cost: upfront and net cost $2,509,600-$3,916,260 (no incentives counted). Annual savings $115,677-$161,022. Simple payback 15.6-33.9 years. Budget strain: over budget (4.2-6.5 times the $600k budget). Backup outage hours 6.8-8.0. Simple payback, not the full SAM model. [2,509,600–3,916,260 USD] — source/calc: `F-C`

## 7. Cost, financing and incentives
*Incentive data is saved sample data (mock, stale, retrieved 2025-10-01). It is not a FACT and is not counted in net cost.*

- **ASSUMPTION** (medium) [A9]: Costs use planning benchmark prices (A9), not quotes. All scenario net costs equal upfront cost because no incentive is counted. — optional source/calc: `F-B`
- **ASSUMPTION** (low) [A5]: Left out of net cost: the federal commercial ITC (listed as open with a placed-in-service deadline of 2027-12-31) and a NY-Sun commercial incentive stand-in (listed as open). Both come from saved mock data retrieved 2025-10-01 that is stale (A5). Their status is uncertain and neither is counted. If confirmed open on official pages, the net cost could be lower. Whether a public school can use the federal credit (for example through direct pay) needs review by tax counsel.
- **RECOMMENDATION** (medium): Recommendation: before committing funds, check each program's current status on the official NYSERDA, IRS and Con Edison pages, and confirm the funding source and fiscal-year timing for the 2027 capital budget. — source/calc: `F-B`

## 8. Priority roadmap

- **RECOMMENDATION** (high): Phase 0, confirm data and budget: get 12-24 months of Con Edison bills, confirm floor area (55,860 vs 17,620 sq ft) and roof area, confirm budget year 2027 and capital type, and confirm the tariff on a bill. — source/calc: `F-B`
- **RECOMMENDATION** (high): Phase 1, professional reviews: structural PE/RA analysis of the roof and a roof condition survey (roof replacement year is unknown). I cannot certify that the roof can hold panels. — source/calc: `F-B`
- **RECOMMENDATION** (medium): Phase 2, efficiency measures: LED lighting and controls first. Estimated cost $223,440-$446,880 and 10-20% savings. — source/calc: `F-A`
- **RECOMMENDATION** (high): Phase 3, permits and interconnection: NYC DOB permits, licensed electrician, FDNY rooftop access review, and a Con Edison interconnection application. — source/calc: `F-B`
- **RECOMMENDATION** (medium): Phase 4, solar installation: about 34 kW DC, sized to the budget left after efficiency quotes (Scenario B). Expand later if funding allows. — source/calc: `F-B`
- **RECOMMENDATION** (medium): Phase 5, battery, commissioning and verification: add a battery if resilience funding is found, commission the system, and check results against bills for at least 12 months. — source/calc: `F-C`

## 9. Resilience and reliability plan
*Battery sizing and hazard ratings are saved sample data (mock), not live results.*

- **ESTIMATE** (low): Scenario C's 120 kW / 960 kWh battery is estimated to cover critical loads for 6.8-8.0 hours in an outage. Critical loads are emergency lighting and communications. The battery size is a saved sample, not a design (A4). [6.8–8 hours] — source/calc: `F-C`
- **ESTIMATE** (medium): Scenarios A and B give no backup power. Solar panels shut off during an outage unless a battery and islanding-capable inverter are installed. [0 hours] — source/calc: `F-B`
- **ASSUMPTION** (low) [A4]: A4: fictional REopt stand-in sized for 8 hours of cooling-center backup. The 120 kW critical load looks well above what emergency lighting and communications need, so the battery is likely oversized for those loads. Re-size it from the real critical-load list.
- **ASSUMPTION** (low) [A6]: Hazard sample lists FEMA flood zone X, low flood rating, moderate heat and winter-storm ratings. This is saved mock data (its note says 'Queens site'), so confirm the flood zone for this Staten Island lot on the official FEMA/NYC map before dropping the flood review.

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): Structural PE/RA analysis of the roof is required. I cannot certify that the roof can hold the panels. — source/calc: `F-B`
- **RECOMMENDATION** (high): A roof condition survey is required. The roof replacement year is unknown. — source/calc: `F-B`
- **RECOMMENDATION** (high): A licensed electrician must design and install the system. FDNY rooftop access and setback review is required. A Con Edison interconnection review and application is required. — source/calc: `F-B`
- **FACT** (medium): No landmark flag was returned for this lot, so no Landmarks Preservation Commission review is added. No parkland flag was returned. If the school sits on parkland, add a parkland use review by counsel. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`

## 11. Path to net-zero and learning resources

- **RECOMMENDATION** (low): Path: efficiency first, then right-sized solar (Scenario B), then expansion toward the whole roof and a battery as budget and incentives allow (Scenario C). On the roof area entered, a larger array could offset more than 100% of annual use. That needs a confirmed roof area and Con Edison export rules. — source/calc: `F-C`
- **RECOMMENDATION** (low): Learning resources: NYSERDA and the NYC School Construction Authority and DOE energy teams publish guidance for schools. I have not retrieved those pages in this run, so none is cited. — source/calc: `F-B`

## 12. Gaps, conflicts and confidence summary

- **FACT** (medium): intake_mismatch:floor_area_sqft: you entered 55,860 sq ft and the city record says 17,620 sq ft (lot area 65,000 sq ft). I used your value. Please confirm. The roof area, efficiency cost and use per sq ft all depend on it. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): missing_field:roof_replaced_year: roof age is unknown, which lowers confidence in the solar and roof-survey scope. — source/calc: `session://profile`
- **FACT** (medium): statewide_average_rate: the electricity price is the New York commercial average, not this school's tariff. Savings confidence is lowered. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ASSUMPTION** (low) [A5]: tariff_needs_user_confirmation and mock_data_in_live_run: the tariff (SC-9 Rate I, General Large, effective 2025-07-01, energy $0.20-$0.24/kWh, demand $18-$24/kW-month) is a fictional saved sample, stale since 2025-10-01. Please confirm your actual tariff on a bill. Demand charges are not in the savings figures.
- **ASSUMPTION** (low) [A6]: mock_data_in_live_run and stale_data: incentives, hazard ratings and battery sizing are saved samples retrieved 2025-10-01, older than the 7-day (incentives) freshness window. They are labeled low confidence and the incentives are left out of net cost.
- **ESTIMATE** (low): The model shows solar alone at 190-209% of annual use, versus the typical 15-25%. Scenario C's reduction above 200% of use and the annual savings assume all solar output is valued at the retail rate. Net metering and export rules were not checked. Treat these as upper bounds. — source/calc: `F-C`
- **ESTIMATE** (low): Scenario B's low end (24.1%) is under the 30% goal and its high end (35.5%) is over it. Whether it meets the goal depends on the efficiency result and the array size, which depend on the unconfirmed floor and roof area. — source/calc: `F-B`

## 13. Sources

- **FACT** (high): Intake profile entered by the user. — source/calc: `session://profile`
- **FACT** (medium): NYC PLUTO tax-lot record (dataset pluto-26v2), retrieved 2026-10-15. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): NREL PVWatts v8 solar production (dataset pvwatts-v8.5.0), retrieved 2026-10-15. — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **FACT** (medium): EIA electricity price data (2026-07, 12-month average), retrieved 2026-10-15. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ESTIMATE** (medium): Cost, payback and scenario figures come from run_financial_model (F-A, F-B, F-C), planning-level and not quotes. — source/calc: `F-A`

---
*All figures are planning-level ESTIMATES with ranges, not quotes and not guarantees of savings. Payback is a simple payback, not the full SAM model. This plan does not certify the roof; a licensed PE or RA must do the structural analysis. Several inputs (floor area, roof area, tariff, incentives, battery size, hazard ratings) need confirmation before any commitment.*
