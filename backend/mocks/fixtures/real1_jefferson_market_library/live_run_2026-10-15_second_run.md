<!-- Live run, second pass, 2026-10-15, after the roof/existing-systems/budget changes: real Claude (claude-sonnet-5-5), TOOL_MODE=live. Records, footprints, PVWatts and EIA are live; the tariff, incentives, hazard and battery tools answered from case 1's saved samples. Status partial BY DESIGN: the roof is pitched, so the solar tools refused until an engineer or roofer verifies the usable area; scenarios B and C are not costed. Check 4 passed. Tool calls: 8, 81.5 s. -->

# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **FACT** (high): Goal: cut grid electricity 30% by 2030 on a $500,000 capital budget (budget year 2027), as you entered it. — source/calc: `session://profile`
- **RECOMMENDATION** (high): Can solar go on the roof? Not yet decided. The roof is pitched, and the sizing tools refuse to size a pitched roof until an engineer or roofer verifies the usable roof area. I therefore give no solar array size, output or savings, and I did not cost Scenarios B or C. The building is also a city landmark, so a Landmarks Preservation Commission (LPC) review is required before any rooftop work. I cannot certify that the roof can hold panels; a licensed PE or RA must do that analysis. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **ESTIMATE** (low): Scenario A (standard efficiency only) is estimated to cost $74,572-$149,144 and to cut grid use 10-20%. That is 33-67% of the way to the 30% goal. It does not reach the goal and it fits within your budget. [10–20 % of annual use] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Rooftop solar alone could not reach 30% in any case, and efficiency alone does not either. Meeting the goal will most likely need deeper efficiency plus verified solar, and what that costs relative to $500,000 is not yet known. Whether to extend the budget is your decision once that gap is compared with the savings. I cannot guarantee savings; every figure is an estimate with a range. — source/calc: `F-A`

## 2. Building profile and data provenance

- **FACT** (high): Jefferson Market Library (NYPL), 425 6th Avenue, Manhattan; library; built 1877; 18,643 sq ft floor area; roof area 7,020 sq ft; pitched roof; Con Edison; annual grid use 268,331 kWh. These are the figures you entered. — source/calc: `session://profile`
- **FACT** (medium): Existing systems: you entered no existing renewables and no existing efficiency work, so the plan assumes none and takes the full benchmark efficiency savings. If any LED, controls or other work is already done, tell me; that would lower the savings and my confidence in them. The baseline for the goal is the 268,331 kWh/yr the building buys from the grid. — source/calc: `session://profile`
- **FACT** (medium): City records (PLUTO) list the lot at 421 Avenue of the Americas, a landmark, built 1877, one building with a 7,019 sq ft footprint, 3 floors, gross floor area 19,800 sq ft. The geocoder matched your address '425 6 Avenue'. The footprint is close to your 7,020 sq ft roof figure, but a footprint is ground area, not a measured roof. [19,800 sq ft gross floor area (city record)] — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (medium): Your Greenwich Village Historic District statement is your own. I did not look up the district designation; only the landmark flag on the city lot record was checked. — source/calc: `session://profile`

## 3. Assumptions register

- **ASSUMPTION** (low) [A5]: A5: Incentive programs and rules come from a mock sample fixture, pending live verification.
- **ASSUMPTION** (low) [A6]: A6: Hazard ratings come from a mock sample fixture, pending site-specific assessment.
- **ASSUMPTION** (medium) [A7]: A7: Efficiency measures (LED and controls) save 10-20% of annual use, from published benchmarks, not a building model. [10–20 % of annual use]
- **ASSUMPTION** (low) [A9]: A9: Planning-level benchmark prices, not quotes: solar $3,000-4,500/kW DC, battery $600-1,000/kWh, standard efficiency $4-8/sq ft saving 10-20%, deep efficiency $10-16/sq ft saving 15-25%; usable battery share 85%-100%; the 30% federal credit counts only when the incentives tool says the program is open. — optional source/calc: `F-A`

## 4. Baseline and efficiency opportunities

- **FACT** (high): Baseline: 268,331 kWh/yr bought from the grid (from your bills/intake, 14.4 kWh per sq ft of your floor area). [268,331 kWh/yr] — source/calc: `session://profile`
- **ESTIMATE** (low): The 30% goal equals about 80,500 kWh/yr less grid use. Standard efficiency (LED and controls) is estimated to cut 26,833-53,666 kWh/yr, which is 10-20% of use. [26,833–53,666 kWh/yr] — source/calc: `F-A`
- **ESTIMATE** (low): Estimated annual savings from Scenario A are $5,316-$12,976. This uses the New York commercial average price of $0.1981-$0.2418/kWh, not this building's own tariff. [5,316–12,976 USD/yr] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Start with LED lighting and controls, since you reported no efficiency work. In a 1877 landmark, interior work is generally easier to permit than exterior work, but confirm with LPC and your design team. — source/calc: `F-A`

## 5. Solar assessment with calculations

- **FACT** (high): Solar sizing refused: the roof is pitched, and the calculation tool will not size a pitched roof from flat-roof defaults. I give no usable roof area, array size, solar kWh or solar savings. — source/calc: `session://profile`
- **RECOMMENDATION** (high): Next step: have an engineer or roofer verify the usable roof area (size, pitch, direction, structure, shading) and enter it in the intake as verified_usable_roof_sqft, then re-plan. Also verify the 7,020 sq ft roof area you entered. Roof replacement year is blank; add it, because panels on a roof near end-of-life usually mean re-roofing first. — source/calc: `session://profile`

## 6. Scenario comparison table

- **ESTIMATE** (low): Scenario A, efficiency only: reduction 10-20% of annual use, which is 33-67% of the goal. Upfront cost $74,572-$149,144. Net cost $74,572-$149,144 (no incentives counted). Simple payback 5.7-28.1 years (not the full SAM model). Budget strain: within budget (15-30% of the $500,000). Outage hours: 0, because there is no backup power. It does not reach the goal. The costs are planning benchmarks, not quotes. [74,572–149,144 USD upfront] — source/calc: `F-A`
- **ESTIMATE** (low): Scenario A: the estimate fits within your budget, so there is no budget gap. About $350,856-$425,428 of the $500,000 would remain for other measures. [350,856–425,428 USD budget remaining] — source/calc: `F-A`
- **RECOMMENDATION** (medium): Scenario B (efficiency plus solar within budget) and Scenario C (deep efficiency, full roof array and battery) were not costed. Both depend on solar output, which depends on the verified usable roof area. They will be compared once that area is entered. Rooftop solar alone typically covers only about 15-25% of annual use and does not reach 30% by itself. That share is not computed for this roof. — source/calc: `session://profile`

## 7. Cost, financing and incentives

- **ESTIMATE** (low): Net cost for Scenario A is $74,572-$149,144 with no incentive counted. [74,572–149,144 USD] — source/calc: `F-A`
- **ASSUMPTION** (low) [A5]: Left out of net cost: the incentives tool returned only mock, stale sample data (retrieved 2025-10-01) listing a federal commercial ITC and a NYSERDA NY-Sun incentive as open. Because that data is a sample and out of date, both are treated as uncertain and are left out of net cost. Eligibility of a public library for a tax credit is also not verified. Confirm current status on official federal and NYSERDA pages before relying on either. — optional source/calc: `https://example.test/fictional/incentives-v0`
- **FACT** (medium): Electricity price used: New York commercial average $0.1981-$0.2418/kWh (12-month average $0.222), EIA, effective 2026-07. This is not the building's own tariff. [0.1981–0.2418 USD/kWh] — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **RECOMMENDATION** (low): Because the full path to 30% is not yet costed, I cannot yet say whether $500,000 is enough. Efficiency at the deep benchmark saves 15-25%, which on its own stays below 30%, so some solar or other reduction is likely needed. Whether to extend the budget is your decision after comparing the gap with the savings. — source/calc: `F-A`

## 8. Priority roadmap

- **RECOMMENDATION** (high): Phase 0, confirm data and budget: confirm the electric bills (268,331 kWh/yr), the budget year and type (2027 capital), the Con Edison tariff, the roof replacement year, and any existing efficiency work. — source/calc: `F-A`
- **RECOMMENDATION** (high): Phase 1, professional reviews: a structural PE/RA analysis, a roof condition survey, and verification of the usable roof area. Begin LPC consultation early. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): Phase 2, efficiency measures: LED lighting and controls (Scenario A package), which can be done first and fit within the budget. — source/calc: `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and Con Edison interconnection application: LPC approval, NYC DOB permits, a licensed electrician, FDNY rooftop access review, and the Con Edison interconnection application. Do this only after the roof is verified. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): Phase 4, solar installation: only if the verified roof area, structural review and LPC approval support it; the array would be sized after re-planning. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): Phase 5, battery, commissioning and verification against bills: size a battery for the critical loads once solar is sized, then check actual results against 12 months of bills. — source/calc: `session://profile`

## 9. Resilience and reliability plan

- **RECOMMENDATION** (medium): Critical loads: reading room cooling and lighting. Scenario A gives no backup power. Scenarios B and C were not run, so there is no battery sizing or outage-hours figure. Solar panels without a battery shut off during an outage, so solar alone would not keep the reading room running. — source/calc: `F-A`
- **ASSUMPTION** (low) [A6]: Hazard context is a mock sample (rated flood zone X, low flood; heat and winter storm moderate) and its note refers to a Queens site, so it is not specific to this building. Treat it as unverified until a real FEMA flood-zone check is done. If the real zone is A, AE, AH, AO, V or VE, equipment must go above the design flood elevation. — optional source/calc: `https://example.test/fictional/hazard-v0`

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): Required: a structural PE/RA analysis (I cannot certify that the roof can hold panels), a roof condition survey, a licensed electrician, FDNY rooftop access review, and a Con Edison interconnection review. — source/calc: `session://profile`
- **RECOMMENDATION** (medium): Landmark review: the city lot record flags this building as a landmark. A Landmarks Preservation Commission (LPC) review is needed before any rooftop or exterior work, including visibility of panels from the street in a historic district. Ask whether the lot is on parkland; if it is, an LPC advisory report to the owning agency applies and counsel must do a parkland use review. The records returned no parkland flag. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **RECOMMENDATION** (high): Pitched roof: output depends on the roof's pitch and direction; a PE or roofer must verify it before any solar sizing. — source/calc: `session://profile`

## 11. Path to net-zero and learning resources

- **RECOMMENDATION** (low): A path toward net-zero would run through efficiency first, then verified rooftop solar, then a battery for the critical loads. On a roof this size, solar is unlikely to cover all of the building's use, so net-zero would also need other measures. Learning resources have not been retrieved in this run. — source/calc: `F-A`

## 12. Gaps, conflicts and confidence summary

- **FACT** (high): Failed or refused tool: the calculation tool (C1) refused to size solar because the roof is pitched and no verified usable roof area exists. Missing because of this: the usable roof area, array size, solar output, solar savings, and Scenarios B and C. The solar production tool was not called, since it would refuse for the same reason. Re-run once verified_usable_roof_sqft is entered. — source/calc: `session://profile`
- **ESTIMATE** (medium): Scenario A was run with placeholder solar inputs because the model requires them; they are zero and do not affect Scenario A, which has no solar. — source/calc: `F-A`
- **FACT** (medium): Address mismatch: you gave 425 6th Avenue; the city lot record lists 421 Avenue of the Americas (it may be another frontage of the same lot). Please confirm. City gross floor area is 19,800 sq ft versus your 18,643 sq ft; I kept your figure. — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **ASSUMPTION** (low) [A5]: Mock and stale data: the hazard, tariff and incentive results are saved sample data from 2025-10-01, and are stale. They are not presented as facts, and their confidence is low. The tariff is a best match named SC-9 Rate I (General Large), effective 2025-07-01, and is not confirmed against a bill; please confirm it. The price used is a statewide average, not this building's tariff. — optional source/calc: `https://example.test/fictional/openei-tariff-v2`
- **FACT** (medium): Roof replacement year is missing from the intake, so the roof's remaining life is unknown. The roof area is your number and should be verified by an engineer or roofer. — source/calc: `session://profile`
- **ASSUMPTION** (low) [A7]: Efficiency savings rest on a published benchmark range (A7) rather than a building model, so confidence is low; an energy audit would firm it up. Payback is a simple payback, not the full SAM model. — optional source/calc: `F-A`

## 13. Sources

- **FACT** (high): Intake profile (user-entered). — source/calc: `session://profile`
- **FACT** (medium): NYC PLUTO tax lot data (building record, landmark flag, footprint). — source/calc: `https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks`
- **FACT** (medium): EIA electricity data browser (New York commercial price). — source/calc: `https://www.eia.gov/electricity/data/browser/`
- **ESTIMATE** (low): Scenario A calculation F-A (run_financial_model, planning-level, not quotes). — source/calc: `F-A`

---
*This is a planning-level estimate, not engineering advice. I cannot guarantee savings. A licensed PE or RA must confirm the roof, and LPC must review any rooftop work, before solar is designed.*
