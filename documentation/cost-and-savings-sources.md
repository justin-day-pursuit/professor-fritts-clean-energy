# Cost and savings sources

Where each price and savings number in the planner comes from, what is verified, and what is still a placeholder.
Researched Oct 16, 2026. Update this file whenever a number changes or a new source is checked.

## Status at a glance

| Number | Status | Source |
| --- | --- | --- |
| Solar cost per kW DC | **Real, live.** Pulled at run time | NYSERDA project data (below) |
| Battery cost per kWh ($600-1,000) | **Placeholder.** Not yet sourced | See "Battery" |
| Efficiency cost per sq ft ($4-8 standard, $10-16 deep) | **Placeholder.** No source found | See "Efficiency" |
| Efficiency savings (10-20% standard, 15-25% deep) | **Placeholder.** Sources found suggest the right size, but none is a typical figure for NYC public buildings | See "Efficiency" |
| Federal credit 30% | Rule, applied only when the incentives tool says the program is open | IRS / program rules |
| Electricity price | **Real, live** | EIA, New York average |
| Solar output | **Real, live** | NREL PVWatts v8 |

## Solar: real, from NYSERDA (in the code)

- Dataset: Solar Electric Programs Reported by NYSERDA, https://data.ny.gov/resource/3x8r-34rs (project cost and nameplate kW for each funded project).
- The code (`backend/tools/solar_costs.py`) takes completed non-residential projects in the five boroughs since 2022-01-01, groups them by size, and uses the 25th to 75th percentile cost per kW DC.
- Checked Oct 16, 2026 (cost per kW DC, 25th / 50th / 75th percentile):
  - up to 100 kW: $3,131 / $3,651 / $4,668 (558 projects)
  - 100-500 kW: $2,528 / $3,000 / $3,752 (239 projects)
  - over 500 kW: $1,996 / $2,356 / $2,930 (35 projects)
- Limits: these are costs of past projects, not quotes. Fewer than 20 projects in a band means the old placeholder is used and flagged.

## Battery: not yet sourced

What the search found (read these from the source before using any number):

- NREL Annual Technology Baseline (ATB), commercial battery storage: https://atb.nlr.gov/electricity/2025/commercial_battery_storage (older editions at atb.nrel.gov). The 2025 page shows its capital cost only as an image and points to a downloadable ATB data spreadsheet. **No dollar figure was read from it.** Next step: download that spreadsheet and read the commercial battery rows.
- The 2024 ATB edition was reported (by a search summary, not read directly) as listing ex-factory lithium-ion prices of about $164-215 per kWh in 2022 dollars, depending on duration. That is equipment only, not installed, so it is not usable as our price.
- A 2021 ATB edition was reported as $480 per kWh for a commercial building-scale system (2019 dollars). It is old and predates recent price changes.
- Not usable: BloombergNEF's global figure is for utility-scale projects in $/MWh.

Until the ATB spreadsheet is read, the battery price stays a labeled placeholder.

## Efficiency: placeholders; partial evidence

What the search found:

- LBNL meta-analysis of lighting controls (240 savings estimates from 88 sources, 2012): average savings of 24% (occupancy sensors), 28% (daylighting), 31% (personal tuning), 36% (institutional tuning), 38% (combined). Lighting only. https://eta-publications.lbl.gov/bibcite/reference/23139
- PNNL, DOE-sponsored (2017): up to 30% of building energy could be avoided with better sensing and controls. This is a modeled potential, and the report says few studies document actual savings. https://www.pnnl.gov/publications/energy-savings-potential-improved-building-controls-us-commercial-building-sector
- DOE project page: 20-30% potential for small and medium commercial buildings with low-cost sensors and retrofit building automation. https://www.energy.gov/eere/buildings/articles/advanced-building-control-solutions
- NYC Local Law 87 (energy audits and retro-commissioning for city buildings): DCAS reports implemented measures dropped energy use by 10% in projects operating a year or more (FY2014 report). A 7-year simple payback is the law's threshold. Reports: https://www.nyc.gov/assets/dcas/downloads/pdf/energy/reportsandpublication/local-law-87-annual-report-fy-2022.pdf (other years are at the same path). This is the closest evidence to our 10-20% standard range, and it points to the low end.
- NYSERDA case study (one building, Brockport): LED retrofit cut connected load about 61%, cost $69,143, payback 1.34 years with incentives. One building; not a typical figure.
- **Cost per sq ft: no reliable source found.** The figures seen came from low-quality generic or industrial guides. Do not use them.

What this means: the 10-20% standard range is plausible but unproven for NYC public buildings, and the cost per sq ft has no source. Best next sources to read directly: the DCAS Local Law 87 annual reports (cost and savings tables), and NYSERDA's commercial lighting and controls program pages.

## Other numbers worth keeping

- NYC public data used by the planner (all free, no key): PLUTO tax lots, building footprints, Local Law 84 energy benchmarking (measured annual kWh), Local Law 24 solar readiness (roof condition and age, owning agency), FEMA National Flood Hazard Layer (flood zone).
