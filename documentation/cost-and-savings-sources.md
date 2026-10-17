# Cost and savings sources

Where each price and savings number in the planner comes from, what is verified, and what is still a placeholder.
Researched Oct 16, 2026. Update this file whenever a number changes or a new source is checked.

## Status at a glance

| Number | Status | Source |
| --- | --- | --- |
| Solar cost per kW DC | **Real, live.** Pulled at run time | NYSERDA project data (below) |
| Battery cost per kWh | **Real, live.** NYSERDA NYC storage projects (placeholder $600-1,000 only if the lookup fails) | See "Battery" |
| Efficiency cost | **Real, live.** Cost per kWh saved from completed NYC public-sector projects (placeholder $4-8 and $10-16 per sq ft only if the lookup fails) | See "Efficiency" |
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

## Battery: real, from NYSERDA (in the code), cross-checked with NREL

- Dataset: Residential, Retail and Bulk Energy Storage Incentive Programs Reported by NYSERDA, https://data.ny.gov/resource/ugya-enpy.
- The code (`backend/tools/solar_costs.py`, `fetch_storage_cost_range`) uses "Retail Storage" (commercial-scale) projects in the five boroughs with status Completed or Approved and a cost above 0, and takes the 25th to 75th percentile of total project cost per kWh AC. Fewer than 20 projects means the placeholder is used and flagged.
- Checked Oct 16, 2026: **$546 / $687 / $812 per kWh** (25th / 50th / 75th percentile, 56 NYC projects).
- Cross-check, NREL Annual Technology Baseline 2025, Commercial Battery Storage, lithium-ion, "Moderate" scenario, 2025 capital cost (installed, national, 2024 dollars not stated in the file): 1 hr $786/kWh, 2 hr $528/kWh, 4 hr $400/kWh, 6 hr $357/kWh, 8 hr $335/kWh (the file gives $/kW: 785.7, 1056.8, 1599.1, 2141.4, 2683.7). NYC projects cost more than the national figure and are mostly short-duration, so the NYC numbers above are the ones used.
- NREL data file (no need to re-download the web pages): https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/csv/2025/v1.0.0/ATBe.csv (320 MB; filter `technology_alias` = "Commercial Battery Storage", `core_metric_parameter` = "CAPEX", `scenario` = "Moderate"). Page: https://atb.nlr.gov/electricity/2025/commercial_battery_storage.
- Limits: these are past project costs (some Approved projects carry estimated costs), not quotes. The price per kWh does not change with how many hours of backup the system gives; NREL shows short systems cost more per kWh.

## Efficiency: cost is real (in the code); savings percent is still a placeholder

**Cost, from NYSERDA's "Energy Efficiency Completed Projects: Beginning 1987"** (https://data.ny.gov/resource/erjw-j2zx, mostly New York Power Authority work for public customers; 2,942 projects, 768 of them schools).
- The code (`backend/tools/efficiency_costs.py`) takes the New York City projects completed since 2016 and reports the 25th / 50th / 75th percentile **cost per kWh saved per year**, so a package costs (kWh it saves) x (that price).
- Checked Oct 16, 2026:
  - LED lighting (stands for "standard" efficiency): $1.17 / $2.56 / $4.02 per kWh saved a year (139 projects). Median simple payback was about 16.6 years.
  - Comprehensive (stands for "deep" efficiency): $1.09 / $2.49 / $3.83 (42 projects). Median payback about 14 years.
- Limits: a project's cost may also cover gas or oil savings that the kWh figure leaves out, which makes the cost per kWh look high for electricity alone. The dataset has no baseline use per project, so it cannot give a savings percent. Fewer than 20 projects in a category means the placeholder dollars per square foot ($4-8 standard, $10-16 deep) are used and flagged.
- Cross-check: our old placeholder worked out to about $1.90-7.70 per kWh saved for P.S. 236, a little higher than the real middle half ($1.17-4.02).

**Savings percent: still a placeholder (10-20% standard, 15-25% deep).** Evidence found, none specific to a NYC public building:
- LBNL meta-analysis of lighting controls (240 estimates, 88 sources, 2012): 24-38% savings, lighting only. https://eta-publications.lbl.gov/bibcite/reference/23139
- PNNL, DOE-sponsored (2017): up to 30% of building energy avoidable with better sensing and controls; a modeled potential, and few studies document actual savings. https://www.pnnl.gov/publications/energy-savings-potential-improved-building-controls-us-commercial-building-sector
- DOE: 20-30% potential for small and medium commercial buildings. https://www.energy.gov/eere/buildings/articles/advanced-building-control-solutions
- NYC Local Law 87 (DCAS): completed projects cut energy use by 10% in the FY2014 report, with a 7-year simple payback threshold. Reports: https://www.nyc.gov/assets/dcas/downloads/pdf/energy/reportsandpublication/local-law-87-annual-report-fy-2022.pdf (the fetch tool could not read these compressed PDFs; read them in a PDF viewer).
- To turn this into a sourced number: read the Local Law 87 tables for measured percent savings by measure.

## Other numbers worth keeping

- NYC public data used by the planner (all free, no key): PLUTO tax lots, building footprints, Local Law 84 energy benchmarking (measured annual kWh), Local Law 24 solar readiness (roof condition and age, owning agency), FEMA National Flood Hazard Layer (flood zone).
