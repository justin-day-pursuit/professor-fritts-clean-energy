# Professor Fritts — Priority roadmap

## 1. Summary and goal status

- **ESTIMATE** (medium): Your goal is a 30% cut in grid electricity by 2030 on an $800,000 capital budget. Rooftop solar alone covers only about 22-24% of annual use, so it does not reach the goal by itself. [22.1–24.3 % of annual use] — calculation `F-B`
- **ESTIMATE** (low): Scenario A (standard efficiency only) does not reach the goal. It cuts about 10-20% of annual use, which is 33-67% of the goal, and costs about $175,040-$350,080. [10–20 % of annual use] — calculation `F-A`
- **ESTIMATE** (low): Scenario B (standard efficiency plus the whole-roof 85.5 kW solar array) reaches the goal at the low end. It cuts about 32.1-44.3% of annual use. Its upfront cost is $442,740-$749,194, within the $800,000 budget. This depends on the efficiency savings placeholder (A7), so confidence is low-medium. [32.1–44.3 % of annual use] — calculation `F-B`
- **ESTIMATE** (low): Scenario C (deep efficiency, whole-roof solar and a 412 kWh backup battery) reaches the goal. It cuts about 37.1-49.3% of annual use. It costs $130,252-$633,818 more than your budget. Meeting the goal with backup power may take more than the amount set aside. Whether to extend the budget is your decision once you have compared the gap with the savings. [37.1–49.3 % of annual use] — calculation `F-C`
- **FACT** (high): Before relying on any solar scenario, note that the city's own solar-readiness record rates this roof 'Not Solar Ready'. Its roof age is 20 years or more and its condition is 'Fair'. Roof repair or replacement is not in these costs. — [source](https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh)

## 2. Building profile and data provenance

- **FACT** (high): You entered P.S. 236 Langston Hughes (DOE building X173), an elementary school at 1871 Walton Avenue, Bronx. It is 43,760 sq ft, was built in 1994, and has a flat roof of 10,260 sq ft. Con Edison is the utility. The budget is $800,000 capital for 2027. — source: `session://profile`
- **FACT** (high): Your annual grid use is 456,834 kWh. The city's Local Law 84 report for 2024 shows the same electricity figure, so I treat it as measured and used no benchmark. [456,834 kWh/yr] — [source](https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-Local-Law-84/5zyy-y8am)
- **FACT** (medium): You told us there is no existing solar or other renewable system and no existing efficiency work. The plan assumes none already on the building. Please confirm this, because already-completed work would lower the efficiency savings. — source: `session://profile`
- **RECOMMENDATION** (high): The baseline for the goal is the electricity the building buys from the grid. — calculation `F-B`
- **FACT** (medium): City building footprints show one building of 10,255 sq ft on the lot. That is close to your roof area of 10,260 sq ft. A footprint is ground area, not a measured roof, so the roof area is your number and needs engineer or roofer verification. [10,255 sq ft] — [source](https://data.cityofnewyork.us/City-Government/Building-Footprints/5zhs-2jue)
- **FACT** (medium): The city lot record is listed under 1869 Walton Avenue, not 1871, and shows 46,700 sq ft gross floor area. Your entry and the Local Law 84 report both say 43,760 sq ft. I kept your 43,760 sq ft. Please confirm the address and floor area. [43,760–46,700 sq ft] — [source](https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks)
- **FACT** (medium): Electricity prices are the New York commercial statewide average, not this building's own tariff: $0.1981-$0.2418 per kWh over 12 months (EIA). [0.1981–0.2418 USD/kWh] — [source](https://www.eia.gov/electricity/data/browser/)

## 3. Assumptions register

- **ASSUMPTION** (medium) [A1]: A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ASSUMPTION** (medium) [A2]: A2: usable roof setback factor 0.55 (C1). — optional source/calc: `C1`
- **ASSUMPTION** (medium) [A3]: A3: array density factor 66 sq ft per kW DC (C2). — optional source/calc: `C2`
- **ASSUMPTION** (low) [A4]: A4: Critical load not given, so estimated at 1.0 W per sq ft x 43,760 sq ft = 43.8 kW (a team placeholder, not metered). Backup length not given, so 8 hours assumed. Battery energy = kW x hours / 0.85 round-trip efficiency = 412 kWh.
- **ASSUMPTION** (low) [A7]: A7: Efficiency measures (LED and controls) save 10-20% of annual use. This is a team planning placeholder, not a cited benchmark and not a building model.
- **ASSUMPTION** (low) [A9]: A9: Planning-level benchmark prices, not quotes. Solar and battery prices come from NYSERDA data on completed NYC projects. Efficiency prices ($4-8/sq ft standard, $10-16/sq ft deep) and savings (10-20% standard, 15-25% deep) are team placeholders, not yet sourced.

## 4. Baseline and efficiency opportunities

- **ESTIMATE** (high): Baseline grid use is 456,834 kWh per year. A 30% cut means about 137,050 kWh per year. [137,050 kWh/yr] — calculation `F-A`
- **ESTIMATE** (low): Standard efficiency (such as LED lighting and controls) is estimated to cut 45,683-91,367 kWh per year (10-20%). It costs $175,040-$350,080. Because you reported no existing efficiency work, these measures are not already in place. Treat the savings as a rough placeholder. [45,683–91,367 kWh/yr] — calculation `F-A`
- **ESTIMATE** (low): Deep efficiency is estimated at $437,600-$700,160 (placeholder $10-16/sq ft), with 15-25% savings, used in Scenario C. [437,600–700,160 USD] — calculation `F-C`
- **FACT** (high): The Local Law 84 report shows natural gas (893,000 kBtu) and fuel oil (69,276 kBtu) use. Heating fuel is therefore mostly outside an electricity-only goal. These fuels are not covered by the 30% grid-electricity target. [893,000 kBtu natural gas] — [source](https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-Local-Law-84/5zyy-y8am)

## 5. Solar assessment with calculations

- **ESTIMATE** (medium): Usable roof is estimated at about 5,643 sq ft (10,260 sq ft x 0.55 setback). [5,643 sq ft] — calculation `C1`
- **ESTIMATE** (medium): That area fits an array of about 85.5 kW DC. [85.5 kW DC] — calculation `C2`
- **ESTIMATE** (medium): PVWatts estimates 101,100-111,098 kWh per year, with a central value of about 106,101 kWh, from a fixed 10-degree south-facing array. [101,100–111,098 kWh/yr] — [source](https://developer.nlr.gov/docs/solar/pvwatts/v8/)
- **ASSUMPTION** (medium) [A1]: The low-high range comes from A1: system losses of 18% (low) to 10% (high) around PVWatts' 14% default; weather is typical-year data.
- **ESTIMATE** (medium): Solar would offset about 23.2% of annual use at the central output. It does not reach the 30% goal alone. [0.2323 fraction of annual use] — calculation `C3`
- **ESTIMATE** (medium): Gross solar bill savings are about $20,028-$26,864 per year (low kWh at the low price, high kWh at the high price). [2.003e+04–2.686e+04 USD/yr] — calculation `C4`
- **RECOMMENDATION** (high): The city's solar-readiness record for this site says 'Not Solar Ready', with a roof of 20 years or more and 'Fair' condition. Check the roof, and consider replacing it, before solar. Roof area, structure and shading all need engineer or roofer verification. — [source](https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh)

## 6. Scenario comparison table

- **ESTIMATE** (low): Scenario A, efficiency only: reduction 10-20% of use (33-67% of the goal); upfront and net cost $175,040-$350,080; payback 7.9-38.7 years; within budget (22-44% of it); outage hours 0. It does not reach the goal. [175,040–350,080 USD net cost] — calculation `F-A`
- **ESTIMATE** (low): Scenario B, efficiency plus solar: reduction 32.1-44.3% of use (107-148% of the goal); upfront $442,740-$749,194; net cost after the federal credit $362,430-$629,460; payback 7.4-21.6 years; within budget (55-94% of it); outage hours 0. It reaches the goal at the low end. Annual savings are about $29,078-$48,956. [362,430–629,460 USD net cost] — calculation `F-B`
- **ESTIMATE** (low): Scenario C, deep efficiency, full solar and battery: reduction 37.1-49.3% of use (124-164% of the goal); upfront $930,252-$1,433,818; net cost $782,457-$1,213,721; payback 14.4-36.1 years; outage hours 8-9.4. It reaches the goal and costs $130,252-$633,818 more than your budget. Reaching the goal with backup may take more than the budget. Whether to extend it is your decision once you have compared the gap with the savings. [782,457–1,213,721 USD net cost] — calculation `F-C`
- **ESTIMATE** (medium): Rooftop solar alone is only about 22-24% of annual use and does not reach the goal by itself. No scenario produces surplus solar, so none is credited or exported. [22.1–24.3 % of annual use] — calculation `F-B`
- **ESTIMATE** (medium): Paybacks are simple paybacks, not the full SAM model. Your budget is a capital budget, treated as one upfront total and not modeled year by year. — calculation `F-B`

## 7. Cost, financing and incentives

- **ESTIMATE** (low): Scenario B, standard efficiency package: $175,040-$350,080 (43,760 sq ft x $4-8/sq ft). This is a team placeholder price (A9). [175,040–350,080 USD] — calculation `F-B`
- **ESTIMATE** (medium): Scenario B, rooftop solar: $267,700-$399,114 (85.5 kW DC x $3,131-4,668/kW). This is the 25th-75th percentile cost per kW of 558 completed NYC non-residential projects of 25-100 kW since 2022, from NYSERDA data. [267,700–399,114 USD] — calculation `F-B` and [source](https://data.ny.gov/Energy-Environment/Solar-Electric-Programs-Reported-by-NYSERDA-Beginn/3x8r-34rs)
- **ESTIMATE** (low): Scenario B, federal credit: minus $80,310 to $119,734 (30% of solar). It is counted only because the snapshot of official pages, retrieved 2026-10-16, shows federal elective pay (direct pay) for governmental entities as open. The statute requires solar to be placed in service by 2027-12-31, a tight schedule given the reviews needed. A DOE school's eligibility is not confirmed here. If the credit is lost, Scenario B upfront cost is $442,740-$749,194. [-119,734–-80,310 USD] — calculation `F-B` and [source](https://www.irs.gov/credits-deductions/elective-pay-and-transferability)
- **ESTIMATE** (low): Scenario B net cost is $362,430-$629,460. [362,430–629,460 USD] — calculation `F-B`
- **ESTIMATE** (low): Scenario C, deep efficiency: $437,600-$700,160 (placeholder, A9). Solar: $267,700-$399,114 (NYSERDA percentile range above). Backup battery: $224,952-$334,544 (412 kWh x $546-812/kWh, 25th-75th percentile of 56 NYC commercial-scale storage projects, NYSERDA data). Federal credit: minus $147,796 to $220,097 (30% of solar and battery). [782,457–1,213,721 USD net cost] — calculation `F-C` and [source](https://data.ny.gov/Energy-Environment/Residential-Retail-and-Bulk-Energy-Storage-Incentive/ugya-enpy)
- **FACT** (low): The NYC Solar Schools program (DCAS, NYPA, NYC Public Schools; solar under power purchase agreements) is uncertain: it is not known whether this building is in the pipeline. It is left out of net cost. Ask DCAS or the SCA whether the school is in it, since it could change the plan. — [source](https://www.nyc.gov/site/dcas/news/010-26/nycps-dcas-complete-130-solar-installations-city-school-roofs-latest-completion-marie)
- **FACT** (low): The NYSERDA NY-Sun commercial incentive for the Con Edison region is uncertain: its status could not be confirmed from an official page on 2026-10-16. It is left out of net cost. — [source](https://www.nyserda.ny.gov/All-Programs/NY-Sun/Contractors/Dashboards-and-incentives/ConEd-Dashboard)
- **FACT** (medium): NYC Local Laws 92 and 94 of 2019 are rules, not incentives. If the roof undergoes certain major renovations, it must have a solar photovoltaic system, a green roof, or both. Check this if roof replacement is needed. — [source](https://www.nyc.gov/site/buildings/dob/pr-sustainable-roof-requirements.page)

## 8. Priority roadmap

- **RECOMMENDATION** (high): Phase 0, confirm data and budget: gather recent Con Edison bills and the tariff, confirm the address and floor area, and confirm the budget year and type (a capital budget treated as one total). Also confirm the roof replacement year, since it is missing from the intake. — source: `session://profile`
- **RECOMMENDATION** (high): Phase 1, professional reviews: hire a structural PE or RA and a roof condition survey before design. Roof area, pitch, structure and shading all need verification. Decide on roof repair or replacement first. — [source](https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh)
- **RECOMMENDATION** (low): Phase 2, efficiency measures: install the standard efficiency package (such as LED and controls) first. It is estimated to cut 10-20% of use at $175,040-$350,080. — calculation `F-A`
- **RECOMMENDATION** (medium): Phase 3, permits and interconnection: file the Con Edison interconnection application for the planned 85.5 kW array. Use a licensed electrician and arrange FDNY rooftop access. Go through DCAS, NYC Public Schools or the SCA for approval. — calculation `C2`
- **RECOMMENDATION** (low): Phase 4, solar installation: install the whole-roof array of about 85.5 kW DC (Scenario B). Aim for in-service before 2027-12-31 if relying on the federal credit. — calculation `F-B`
- **RECOMMENDATION** (low): Phase 5, battery, commissioning and verification: if you extend the budget, add the 412 kWh battery (Scenario C). Either way, commission the system and compare real bills against these estimates. — calculation `F-C`

## 9. Resilience and reliability plan

- **ESTIMATE** (low): Scenario C gives about 8-9.4 outage hours of backup for the critical loads you named, emergency lighting and communications. [8–9.4 hours] — calculation `F-C`
- **ESTIMATE** (medium): Scenarios A and B give no backup power. Solar panels shut off in an outage without a battery. [0 hours] — calculation `F-B`
- **ASSUMPTION** (low) [A4]: A4: Critical load not given, so estimated at 1.0 W per sq ft x 43,760 sq ft = 43.8 kW (a team placeholder, not metered). Backup length not given, so 8 hours assumed. Battery energy = kW x hours / 0.85 round-trip efficiency = 412 kWh. Give us the real critical load and backup hours to resize.
- **FACT** (medium): FEMA's current effective flood map shows zone X (area of minimal flood hazard) at this address. Heat and winter-storm ratings were not looked up, and the 2015 preliminary flood map was not checked, so I give no ratings for them. — [source](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28)

## 10. Required professional reviews and permits

- **RECOMMENDATION** (high): A licensed structural PE or RA must do the structural analysis. I cannot certify that the roof can hold the panels. A roof condition survey is also required, given the 'Not Solar Ready' status and the 20-year-plus roof age. — [source](https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh)
- **RECOMMENDATION** (high): Mandatory reviews also include a licensed electrician, FDNY rooftop access review, and a Con Edison interconnection review for the 85.5 kW array. The list at the end of the plan has the links. — calculation `C2`
- **RECOMMENDATION** (medium): The owner agency is DOE, so approval goes through DCAS, NYC Public Schools or the SCA. — [source](https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh)
- **FACT** (medium): The city record shows no landmark flag, and the flood zone is X. No Landmarks Preservation Commission review or flood-zone review is triggered by these records. Check whether the 2015 preliminary map changes this. — [source](https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks)

## 11. Path to net-zero and learning resources

- **RECOMMENDATION** (low): Net-zero is not reached by any scenario here. Solar covers about 22-24% of grid use. Gas and fuel oil heating are outside the electricity goal. A longer path would add heating electrification, which would raise electric use, so plan the roof and electrical service together. — [source](https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-Local-Law-84/5zyy-y8am)
- **FACT** (medium): For learning, the NYC Solar Schools program page describes how DOE schools have added rooftop solar. — [source](https://www.nyc.gov/site/dcas/news/010-26/nycps-dcas-complete-130-solar-installations-city-school-roofs-latest-completion-marie)

## 12. Gaps, conflicts and confidence summary

- **FACT** (high): Missing intake fields: roof replacement year, critical load kW, backup hours, lighting type, cooling type, building controls and heating fuel. Heating fuel is non-electric per the city record. The battery size and the efficiency savings depend on these, so their confidence is low. — source: `session://profile`
- **FACT** (high): Flag city_roof_not_solar_ready: the city's Local Law 24 record says 'Not Solar Ready', roof age 20 years or more, condition Fair. Roof repair or replacement is not costed and could change the budget picture. — [source](https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh)
- **FACT** (high): Flag statewide_average_rate: prices are the New York commercial average, not this building's own tariff. Please confirm the tariff against a bill. — [source](https://www.eia.gov/electricity/data/browser/)
- **FACT** (high): Flag hazard_partial: only the current FEMA flood zone was read. Heat and winter-storm ratings and the 2015 preliminary map were not checked. — [source](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28)
- **ASSUMPTION** (low) [A4]: Flag battery_inputs_estimated: the battery size rests on a placeholder critical load and an assumed 8 hours (A4).
- **ASSUMPTION** (low) [A7]: The efficiency prices and savings (A7, A9) are team placeholders, so whether Scenario B reaches 30% is low confidence. Scenario A's low end and the solar-only share are below the goal.
- **FACT** (medium): The incentive snapshot dated 2026-10-16 is fresh. The federal credit is counted as open but has a 2027-12-31 in-service deadline and unconfirmed DOE eligibility. NY-Sun and NYC Solar Schools are uncertain and left out of net cost. — [source](https://www.irs.gov/credits-deductions/elective-pay-and-transferability)
- **FACT** (medium): The city lot record uses address 1869 Walton Avenue and a floor area of 46,700 sq ft, against your 1871 Walton Avenue and 43,760 sq ft. I kept your values. Please confirm both. — [source](https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks)

## 13. Sources

- **FACT** (high): Data used: your intake, NYC PLUTO, Building Footprints, Local Law 84 and Local Law 24 records, NREL PVWatts, EIA prices, NYSERDA cost data, the incentives snapshot dated 2026-10-16, and the FEMA flood map. The system adds the source links list at the end of the plan. — source: `session://profile`

## Who to contact and where to start

- [NYC Department of Education route: DCAS Energy Management](https://www.nyc.gov/site/dcas/agencies/energy-management.page): DCAS runs energy projects for city buildings; for a public school, start here before buying solar.
- [NYC School Construction Authority (SCA)](https://www.nycsca.org/): The SCA builds and repairs public school buildings, including roofs; roof work and solar on a school go through it.
- [NYC Public Schools](https://www.schools.nyc.gov/): The school system's facilities staff approve changes to a school building.
- [NYC Department of Buildings: Local Laws 92 and 94 (solar and green roofs)](https://www.nyc.gov/site/buildings/codes/ll92-solar-green-roofs.page): Replacing a roof triggers a rule to cover it with solar, a green roof, or both; plan the roof and solar together.
- [Con Edison: connecting solar to the grid](https://www.coned.com/en/save-money/using-distributed-generation-energy-sources/solar-energy/information-for-contractors): Every solar array needs a Con Edison interconnection application (a small or a large portal, depending on size). Contact: Con Edison Distributed Generation: dgexpert@coned.com.
- [Con Edison Solar Photovoltaics Guide (PDF)](https://www.coned.com/-/media/files/coned/documents/save-energy-money/using-private-generation/solar-photovoltaics-guide.pdf): The utility's own steps, fees and timelines for connecting solar.
- [Con Edison Energy Storage System Guide (PDF)](https://www.coned.com/-/media/files/coned/documents/save-energy-money/using-private-generation/specs-and-tariffs/energy-storage-guide.pdf): A battery has its own connection rules; this is the utility's guide for them.
- [NYC Department of Buildings](https://www.nyc.gov/site/buildings/index.page): Permits for solar, batteries and roof work are filed here, by a registered design professional and a licensed electrician.
- [FDNY](https://www.nyc.gov/site/fdny/index.page): Rooftop solar and battery systems must meet FDNY access and safety rules.
- [NYSERDA NY-Sun](https://www.nyserda.ny.gov/All-Programs/NY-Sun): The State's solar incentive program; confirm whether a public building can use it before counting any incentive.
- [NYC Accelerator](https://accelerator.nyc/): A city program that helps building owners with energy upgrades and compliance.

## Source links

Every page the numbers and rules in this plan rest on:
- [lookup_ny_building_records](https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks), retrieved 2026-10-17
- [NYC building footprints](https://data.cityofnewyork.us/City-Government/Building-Footprints/5zhs-2jue), retrieved 2026-10-17
- [NYC Local Law 84 energy report](https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-Local-Law-84/5zyy-y8am), retrieved 2026-10-17
- [NYC Local Law 24 solar readiness](https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh), retrieved 2026-10-17
- [get_solar_production](https://developer.nlr.gov/docs/solar/pvwatts/v8/), retrieved 2026-10-17
- [get_utility_rates](https://www.eia.gov/electricity/data/browser/), retrieved 2026-10-17
- [search_ny_incentives_and_rules](https://www.irs.gov/credits-deductions/elective-pay-and-transferability), retrieved 2026-10-16
- [Federal elective pay (direct pay) for governmental entities, solar investment credit (IRC 6417 / 48E) (statute or rule text)](https://www.law.cornell.edu/uscode/text/26/48E), retrieved 2026-10-16
- [NYC Solar Schools program (DCAS, NYPA, NYC Public Schools): rooftop solar on DOE schools under power purchase agreements](https://www.nyc.gov/site/dcas/news/010-26/nycps-dcas-complete-130-solar-installations-city-school-roofs-latest-completion-marie), retrieved 2026-10-16
- [NYSERDA NY-Sun commercial and industrial solar incentive (Con Edison region)](https://www.nyserda.ny.gov/All-Programs/NY-Sun/Contractors/Dashboards-and-incentives/ConEd-Dashboard), retrieved 2026-10-16
- [NYC Local Laws 92 and 94 of 2019 (sustainable roofs): rule, not an incentive](https://www.nyc.gov/site/buildings/dob/pr-sustainable-roof-requirements.page), retrieved 2026-10-16
- [get_hazard_context](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28), retrieved 2026-10-17
- [NYSERDA solar project costs](https://data.ny.gov/Energy-Environment/Solar-Electric-Programs-Reported-by-NYSERDA-Beginn/3x8r-34rs), retrieved 2026-10-17
- [NYSERDA battery storage project costs](https://data.ny.gov/Energy-Environment/Residential-Retail-and-Bulk-Energy-Storage-Incentive/ugya-enpy), retrieved 2026-10-17

---
*All figures are planning estimates with ranges, not quotes, and nothing here is a guarantee of savings. A licensed PE or RA must confirm the roof and structure before any solar work. Payback figures are simple payback, not the full SAM model.*
