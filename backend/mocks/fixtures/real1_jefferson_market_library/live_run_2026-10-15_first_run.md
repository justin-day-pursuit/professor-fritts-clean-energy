<!-- Live run on 2026-10-15: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools have no live version and answered from case 1's saved samples (so the hazard note says Queens). Status done; Check 4 passed on the first try. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **RECOMMENDATION** (medium): Short answer on the roof: solar may be possible, but I cannot confirm it. The city record flags this lot as a landmark, so a Landmarks Preservation Commission (LPC) permit review is needed before any rooftop or exterior work. A licensed PE or RA must also do the structural analysis. I cannot certify that the roof can hold panels. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **ESTIMATE** (medium): Rooftop solar alone (full 55 kW DC array) covers only about 24.7-27.1% of annual use. It does not reach the 30% goal by itself. [24.7–27.1 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (standard efficiency + the 55 kW roof array) is estimated to cut 34.7-47.1% of grid use at a net cost of $239,572-$396,644. That is inside the $500,000 budget, and the low end of the range reaches the 30% goal. It depends on LPC and structural approval for the roof array. [34.7–47.1 % of annual use] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario A (efficiency only) is estimated to cut 10-20% of use, which is 33-67% of the goal. It does not reach the goal. It is the fallback if LPC does not approve rooftop solar. [10–20 % of annual use] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario C (deep efficiency, full solar and battery) is estimated to cost $927,430-$1,505,788, which is 1.85-3.01 times your budget. It is over budget. [927,430–1,505,788 USD] — source/calc: `F-C`
- **RECOMMENDATION** (high): I cannot promise any savings. Every figure here is an estimate with a range, built on planning benchmarks and not on quotes. — source/calc: `F-B`

## 2. Building profile and data provenance

- **FACT** (high): You entered: Jefferson Market Library (NYPL), 425 6th Avenue, Manhattan; library; 18,643 sq ft; built 1877; pitched roof with clock tower; roof area 6,600 sq ft; Con Edison; annual use 268,331 kWh; capital budget $500,000 for 2027; critical loads are reading room cooling and lighting. — source/calc: `session://profile`
- **FACT** (medium): The NYC PLUTO record lists the lot as 421 Avenue of the Americas (BBL 1006060001), gross floor area 19,800 sq ft, lot area 26,747 sq ft, 3 floors, built 1877, with landmark_flag true. The street differs from your 425 6th Avenue. It may be another frontage of the same lot, so please confirm. Its floor area also differs from your 18,643 sq ft. I kept your figure as the working value; please confirm which is right. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): The roof replacement year was left blank, so roof age is unknown. — source/calc: `session://profile`

## 3. Assumptions register

- **ASSUMPTION** (medium) [A1]: A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ASSUMPTION** (medium) [A2]: A2: usable roof setback factor 0.55. — optional source/calc: `C1`
- **ASSUMPTION** (medium) [A3]: A3: array density 66 sq ft per kW DC. — optional source/calc: `C2`
- **ASSUMPTION** (low) [A4]: A4: fictional REopt stand-in sized for 8 hours of cooling-center backup (sample data, not a site design).
- **ASSUMPTION** (low) [A5]: A5: incentive programs and rules come from a mock sample fixture, pending live verification.
- **ASSUMPTION** (low) [A6]: A6: hazard ratings come from a mock sample fixture, pending site-specific assessment.
- **ASSUMPTION** (medium) [A7]: A7: efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model.
- **ASSUMPTION** (low) [A9]: A9: planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open. — optional source/calc: `F-A`

## 4. Baseline and efficiency opportunities

- **FACT** (medium): Baseline annual grid use is 268,331 kWh, from your entry. It is not checked against bills. [268,331 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (low): Standard efficiency (LED and controls) is estimated to save 26,833-53,666 kWh/yr, which is 10-20% of use, at an upfront cost of $74,572-$149,144. [26,833–53,666 kWh/yr] — source/calc: `F-A`
- **RECOMMENDATION** (low): Efficiency work inside a landmark building should be scoped by an energy auditor. Interior lighting and controls generally have less LPC exposure than rooftop work, but confirm this with LPC. — source/calc: `F-A`

## 5. Solar assessment with calculations

- **ESTIMATE** (low): Usable roof area is about 3,630 sq ft (6,600 sq ft × 0.55 setback). [3,630 sq ft] — source/calc: `C1`
- **ESTIMATE** (low): Array size is about 55 kW DC (3,630 sq ft ÷ 66 sq ft per kW). A pitched roof with a clock tower may fit less than this. [55 kW DC] — source/calc: `C2`
- **ESTIMATE** (low): PVWatts estimates annual output of 66,286-72,833 kWh (central 69,563 kWh). The model used a 10° tilt and south-facing orientation, which is generic and not your actual roof geometry. [66,286–72,833 kWh/yr] — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **ASSUMPTION** (medium) [A1]: The range uses A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ESTIMATE** (low): Central solar output is about 25.9% of annual use. [0.2592 fraction of annual use] — source/calc: `C3`
- **ESTIMATE** (low): Annual solar bill savings are about $13,131 (low kWh × low price $0.1981) to $17,611 (high kWh × high price $0.2418). Prices are the New York commercial average, not this building's tariff. [13,131–17,611 USD/yr] — source/calc: `C4`
- **ESTIMATE** (medium): Rooftop solar alone is about 24.7-27.1% of annual use. It does not reach the 30% goal by itself. [24.7–27.1 % of annual use] — source/calc: `F-B`

## 6. Scenario comparison table

- **ESTIMATE** (low): Scenario A (efficiency only): share of goal 33-67%, which is a 10-20% reduction. Upfront and net cost $74,572-$149,144. Simple payback 5.7-28.1 years. Within budget (15-30% of it). Outage hours 0. Does not reach the goal. [74,572–149,144 USD net cost] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario B (efficiency + solar within budget): share of goal 116-157%, which is a 34.7-47.1% reduction. Upfront and net cost $239,572-$396,644. Simple payback 7.8-21.5 years. Within budget (48-79% of it). Outage hours 0. Reaches the goal at the low end, if the roof array is approved. [239,572–396,644 USD net cost] — source/calc: `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency + full solar + 960 kWh battery): share of goal 132-174%, which is a 39.7-52.1% reduction. Upfront and net cost $927,430-$1,505,788. Simple payback 27.4-71.3 years. Over budget (1.85-3.01 times). Outage hours 6.8-8.0. Reaches the goal but is not affordable on $500,000. [927,430–1,505,788 USD net cost] — source/calc: `F-C`
- **ASSUMPTION** (low) [A9]: Payback is a simple payback, not the full SAM model. All costs use planning benchmarks (A9) and are not quotes. — optional source/calc: `F-B`

## 7. Cost, financing and incentives

- **ASSUMPTION** (low) [A5]: No incentive is counted in any net-cost figure, so net cost equals upfront cost in all three scenarios. The incentives tool returned only sample data retrieved 2025-10-01, which is stale and mock. It listed a federal commercial ITC (deadline 2027-12-31) and an NY-Sun commercial incentive as 'open'. That status is unverified and left out of net cost. — optional source/calc: `https://example.test/fictional/incentives-v0`
- **RECOMMENDATION** (low): Whether a public library can claim a federal credit is not established by my sources. Check with your finance office and tax advisor, and check the official program pages before you count any incentive. — source/calc: `F-B`
- **ESTIMATE** (low): The $500,000 capital budget (2027) covers Scenario B's estimated net cost of $239,572-$396,644. That leaves roughly $103,000-$260,000 of headroom for LPC design work, structural review and contingency. Benchmark costs may not include historic-district design requirements. — source/calc: `F-B`
- **FACT** (medium): Electricity prices are the New York commercial average over 12 months through 2026-07: $0.1981-$0.2418/kWh (average $0.222). They are not this building's tariff. [0.1981–0.2418 USD/kWh] — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ASSUMPTION** (low) [A5]: The best-match tariff is Con Edison SC-9 Rate I (General Large), effective 2025-07-01, with energy charges $0.20-$0.24/kWh and demand charges $18-$24/kW-month. This is sample data, stale and unconfirmed. Please confirm it against a bill. — optional source/calc: `https://example.test/fictional/openei-tariff-v2`

## 8. Priority roadmap

- **RECOMMENDATION** (medium): Phase 0, confirm data and budget: collect 12 months of Con Edison bills, confirm the tariff, the floor area (18,643 vs 19,800 sq ft) and the lot address, confirm budget year 2027 and capital type, and find the roof replacement year. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): Phase 1, professional reviews: a licensed structural PE/RA analysis and a roof condition survey for the pitched roof and clock tower. Begin pre-application talks with LPC at the same time, because the outcome decides whether Scenario B is possible. — source/calc: `F-B`
- **RECOMMENDATION** (low): Phase 2, efficiency measures: LED lighting and controls, with the reading-room cooling and lighting as a first priority. Estimated 10-20% reduction. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and interconnection: LPC permit, NYC Department of Buildings permits, a licensed electrician, FDNY rooftop access review, and a Con Edison interconnection application. — source/calc: `F-B`
- **RECOMMENDATION** (low): Phase 4, solar installation: install only the array size that the structural review and LPC allow. It may be smaller than 55 kW DC, which would lower the 30% result. — source/calc: `F-B`
- **RECOMMENDATION** (low): Phase 5, battery, commissioning and verification: a battery is optional and over budget in Scenario C. If added later, commission it and check results against 12 months of bills. — source/calc: `F-C`

## 9. Resilience and reliability plan

- **ESTIMATE** (low): Scenario C's battery (sample sizing 960 kWh, 120 kW) is estimated to give 6.8-8.0 hours of outage backup for the critical loads: reading room cooling and lighting. [6.8–8 hours] — source/calc: `F-C`
- **ASSUMPTION** (low) [A4]: The battery size is a sample figure from a fictional REopt stand-in (A4), sized for 8 hours of cooling-center backup.
- **ESTIMATE** (medium): Scenarios A and B give no backup power. Solar panels shut off during an outage unless a battery is installed. [0 outage hours] — source/calc: `F-B`
- **ASSUMPTION** (low) [A6]: Sample hazard data rates flood zone X (low flood rating), moderate heat and moderate winter-storm risk. This is mock data labeled as a Queens site, so it is not site-specific. Verify the flood zone against FEMA and NYC flood maps before you place any battery or switchgear. — optional source/calc: `https://example.test/fictional/hazard-v0`

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): Landmarks Preservation Commission (LPC) permit review is required before any rooftop or exterior work. The city record flags the lot as a landmark, and you describe it as in the Greenwich Village Historic District. Visibility of panels from the street, and the clock tower roof, are design questions for LPC. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (high): A licensed structural PE or RA must analyze the roof and clock tower. I cannot certify that the roof can hold panels. A roof condition survey is also needed. — source/calc: `F-B`
- **RECOMMENDATION** (high): A licensed electrician must do the work. FDNY rooftop access and setback review is required, and Con Edison utility interconnection review is required. — source/calc: `F-B`
- **RECOMMENDATION** (low): No flood-zone review (NYC Building Code Appendix G) is triggered if the sample zone X is correct. Confirm the zone against official FEMA data. Parkland status was not flagged in the records I retrieved; confirm with counsel if any part of the site is parkland. — source/calc: `https://example.test/fictional/hazard-v0`

## 11. Path to net-zero and learning resources

- **ESTIMATE** (low): Net-zero is not reachable with rooftop solar alone: the roof offsets only about 24.7-27.1% of use. Even Scenario C, with deep efficiency, reaches a 39.7-52.1% reduction. Further steps would be deeper efficiency, electrification planning and possibly off-site renewable supply. These are not modeled here. [39.7–52.1 % of annual use] — source/calc: `F-C`
- **RECOMMENDATION** (low): No learning resources were retrieved in this run, so none are listed. — source/calc: `F-A`

## 12. Gaps, conflicts and confidence summary

- **FACT** (medium): address_street_mismatch: the city record uses 421 Avenue of the Americas, but you entered 425 6th Avenue. The geocoder matched 425 6 Avenue to the same lot (BBL 1006060001) with a fallback match at 0.8 confidence. Please confirm it is the same lot. The solar location and the landmark flag depend on it. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): Floor area differs: you entered 18,643 sq ft and the city's gross floor area is 19,800 sq ft. I used 18,643 sq ft. Please confirm. The lot area (26,747 sq ft) does not match your figure. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): missing_field:roof_replaced_year: roof age is unknown, which lowers confidence in all solar and structural claims. — source/calc: `session://profile`
- **FACT** (medium): statewide_average_rate: electricity prices are the New York commercial average, not this building's tariff. tariff_needs_user_confirmation: SC-9 Rate I (effective 2025-07-01) is a best match and needs a bill to confirm it. The tariff data is mock and stale, with a retrieval date of 2025-10-01. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ASSUMPTION** (low) [A5]: mock_data_in_live_run and stale_data: incentives, hazard, tariff and battery sizing come from saved sample data retrieved 2025-10-01, about a year old and past the 7-day incentive freshness limit. I had no live source to refresh it, so those figures are low confidence. I did not save any of it to the cache, because it is not from an official source. Incentive status is unverified and left out of net cost.
- **ASSUMPTION** (low) [A6]: The hazard sample is labeled as a Queens site, so it is not specific to this Manhattan building.
- **ASSUMPTION** (low) [A2]: Solar output assumes a 10° tilt and south-facing orientation, and a roof area with a 0.55 setback. The real pitched roof, clock tower, shading and LPC limits may reduce the array. Costs are planning benchmarks, not quotes.
- **RECOMMENDATION** (medium): Next steps: send bills, confirm the address and floor area, supply the roof year, then re-run the plan with real incentive and tariff data. Request LPC pre-application feedback and the structural review. — source/calc: `F-B`

## 13. Sources

- **FACT** (high): Your intake profile. — source/calc: `session://profile`
- **FACT** (high): NYC Open Data PLUTO tax lot records (pluto-26v2), retrieved 2026-10-15. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (high): PVWatts v8 solar production, retrieved 2026-10-15. — source/calc: `https://developer.nlr.gov/docs/solar/pvwatts/v8/`
- **FACT** (high): EIA electricity retail price data (2026-07), retrieved 2026-10-15. — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ASSUMPTION** (low) [A5]: Sample tariff, incentives, hazard and battery data (mock, retrieved 2025-10-01), used only as low-confidence context: tariff, incentives, hazard, battery sizing. — optional source/calc: `https://example.test/fictional/incentives-v0`

---
*This plan is a planning-level estimate. It is not a structural certification, a permit determination or a guarantee of savings.*
