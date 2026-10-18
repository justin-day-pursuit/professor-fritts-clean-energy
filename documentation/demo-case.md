# Demo case: P.S. 236 Langston Hughes (the "good case")

A real Bronx elementary school, chosen from NYC's public data as the cleanest example we could find, for the demo and for UI testing. Folder: `backend/mocks/fixtures/demo_ps236_bronx/`. Built Oct 16, 2026.

## Why this building
We searched about 1,500 school records in NYC Open Data for a building where the public sources agree with each other. P.S. 236 passed every filter, and 24 buildings did:

- DOE-owned, flat-roof elementary school, 4 floors, built 1994
- PLUTO (46,700 sq ft) and LL84 (43,760 sq ft) agree within 7%
- three years of steady grid electricity (457k–501k kWh), no solar already installed
- one clean building outline of 10,255 sq ft (the roof area), no landmark or historic district
- FEMA flood zone X, minimal hazard
- the lookups raise no data-mismatch flags at all

The building is DOE building code X173 at 1871 Walton Avenue (PLUTO lists the lot as 1869), BBL 2028510021.

## What the plan says (at an $800,000 capital budget)
- **Scenario B** (LED and controls plus a 85.5 kW roof array) cuts grid use 32–44%, so it reaches the 30% goal even at the low end. It costs $432k–$735k before the federal credit and $355k–$619k after, within the budget. Payback is 7–21 years.
- **Scenario C** (deep efficiency, the same array, plus a backup battery) reaches the goal too, with 6.8–8.0 hours of backup power. It costs $470k–$1.24M more than the budget, so the plan states the gap and says extending the budget is the user's choice.
- Solar alone covers 22–24% of use and cannot reach 30% by itself.
- The plan refers the user to the city's Solar Schools program, because a DOE school may get solar through it without spending this budget.

## What is real and what is not
| Part | Source | Real? |
| --- | --- | --- |
| Building records, roof outline | NYC PLUTO and building footprints, pulled Oct 16, 2026 | Live pull, saved |
| Solar output | PVWatts v8 at the school's location | Live pull, saved |
| Electricity price | EIA New York commercial average (not this building's tariff) | Live pull, saved |
| Flood zone | FEMA effective map, zone X | Real, looked up by hand |
| Incentives and rules | Official pages read by hand on Oct 16, 2026 (see below) | Real snapshot, **goes stale after 7 days** |
| Tariff | Case 1's saved sample (SC-9 Rate I) | **Sample** |
| Battery sizing | Case 1's saved sample (960 kWh, 120 kW) | **Sample** |
| Heat and storm ratings | Not looked up | Missing |
| Budget, critical loads, "none" for existing systems, flat roof | Stated choices | Not public |
| The plan text | Written by us from the real tool numbers | **Scripted, not Claude's own words** |

The plan text is a script we wrote. It passes all four safety checks the same way a live plan would, but it is not a recording of Claude. After one approved live run, `python manage.py record_case --run <id> --case demo_ps236_bronx --overwrite` replaces it with a real recording (about $0.25 with caching).

## Incentives and rules snapshot (read Oct 16, 2026)
| Item | Status in the plan | Official source |
| --- | --- | --- |
| Federal elective pay for government entities (solar credit) | open; solar must be placed in service by 2027-12-31 | IRS elective pay page (updated 2026-06-27); 26 U.S.C. 48E(e)(4) |
| NYC Solar Schools (DCAS, NYPA, NYC Public Schools) | uncertain for this building; 130 done, 86 in progress (Apr 2026), no enrollment process published | NYC DCAS release, 2026-04-23 |
| NYSERDA NY-Sun commercial incentive | uncertain: could not be confirmed (NYSERDA's pages blocked automated access); left out of net cost | NYSERDA Con Edison dashboard |
| NYC Local Laws 92/94 (sustainable roofs) | rule: a re-roof needs solar and/or a green roof | NYC DOB release, 2019-11-15 |

The federal credit is counted at 30% of solar and battery cost in the net cost. It assumes the project is under 1 MW and meets the deadline, and the plan says to confirm both with a tax advisor. The statute's wording about when construction begins comes from a legal-information site (Cornell LII) and the IRS notice PDF could not be read, so a tax advisor should confirm the dates.

## Using it
- Replay (free, instant): `LLM_PROVIDER=scripted TOOL_MODE=mock python manage.py run_case --case demo_ps236_bronx --llm scripted`
- It is also an eval case: `python manage.py run_evals --case demo_ps236_bronx`
- Rebuild after changing the budget or the text: `python mocks/build_demo_case.py` from `backend/`.
- Before a demo more than a week after Oct 16, re-read the incentive pages and update the quotes in `mocks/build_demo_case.py`; the replay will otherwise flag the incentives as stale.

## Sources
- NYC Open Data: PLUTO (`64uk-42ks`), building footprints (`5zhs-2jue`), LL84 (`5zyy-y8am`)
- [IRS: Elective pay and transferability](https://www.irs.gov/credits-deductions/elective-pay-and-transferability); [26 U.S.C. 48E](https://www.law.cornell.edu/uscode/text/26/48E)
- [NYC DCAS: 130 solar installations on school roofs](https://www.nyc.gov/site/dcas/news/010-26/nycps-dcas-complete-130-solar-installations-city-school-roofs-latest-completion-marie)
- [NYC DOB: sustainable roof requirements](https://www.nyc.gov/site/buildings/dob/pr-sustainable-roof-requirements.page)
- [NYSERDA NY-Sun Con Edison dashboard](https://www.nyserda.ny.gov/All-Programs/NY-Sun/Contractors/Dashboards-and-incentives/ConEd-Dashboard) (not readable by our tools on Oct 16)
- [FEMA National Flood Hazard Layer](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer)
- P.S. 236 Langston Hughes at 1871 Walton Avenue: [schools.nyc.gov](https://www.schools.nyc.gov/schools/X236)
