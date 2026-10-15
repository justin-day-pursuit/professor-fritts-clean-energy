# Real-building test cases

Four real NYC public buildings, added Oct 15, 2026, to test Professor Fritts on real addresses and public data instead of fictional buildings. Each has a folder under `backend/mocks/fixtures/` holding:

- `intake.json`: public data where it exists; the rest are stated choices (see below)
- `live/`: what the live tools returned in the second run on Oct 15, 2026 (PLUTO with building footprints, PVWatts, EIA)
- `live_run_2026-10-15_first_run.md` and `live_run_2026-10-15_second_run.md`: the roadmap Claude wrote before and after the roof, existing-systems and budget changes (see "Two passes" below)
- `get_hazard_context.json`: the real FEMA effective flood zone for the site (looked up by hand); heat and storm ratings were not looked up
- `get_utility_tariff.json`, `search_ny_incentives_and_rules.json`, `optimize_solar_storage.json`: copies of case 1's samples, because these tools have no live version yet

They are **not** eval cases yet (no `expected.json`, no scripted run). Run one live from `backend/`:

```bash
TOOL_MODE=live python manage.py run_case --case real2_red_hook_rec_center --llm anthropic --message "<the question in intake.json>"
```

Note that `run_case` loads the folder's `intake.json` as the profile but asks Dana's question unless `--message` is given.

## The buildings

| Folder | Building | BBL | What it tests |
| --- | --- | --- | --- |
| `real1_jefferson_market_library` | Jefferson Market Library (NYPL), 425 6th Ave, Manhattan | 1006060001 | Historic district (LPC review), a pitched 1877 roof with a clock tower |
| `real2_red_hook_rec_center` | Red Hook Recreation Center (NYC Parks), 155 Bay St, Brooklyn | 3005820001 | Parkland, individual landmark (Red Hook Play Center, LP-2241, 2008), basement flooded in Hurricane Sandy while FEMA's effective map says shaded X; existing-systems section left blank on purpose |
| `real3_ps38_staten_island` | P.S. 38 (R038), 421 Lincoln Ave, Staten Island | 5037320006 | A typical school; PLUTO disagrees with LL84 on floor area |
| `real4_ps24_bronx_existing_solar` | P.S. 24 (X024), 660 W 236th St, Bronx | 2059170140 | A roof that already has solar (457,512 kWh made in 2024) |

## Where the inputs come from

| Input | Source |
| --- | --- |
| Annual kWh | LL84 2024, grid electricity purchased (NYC Open Data `5zyy-y8am`) |
| Floor area, year built | LL84 2024 (PLUTO is checked against them during the run) |
| Landmark, historic district, owner | PLUTO (`64uk-42ks`) |
| Flood zone | FEMA National Flood Hazard Layer, effective map |
| Roof area | The intake form's "Suggest roof area from city records" answer: the sum of the building outlines on the tax lot, from NYC building footprints (`5zhs-2jue`), computed from the outline geometry. **Not a measured roof**: 7,020 / 32,860 / 34,360 / 40,500 sq ft. Verify with an engineer or roofer. |
| Roof type | Stated choice from aerial imagery; Jefferson Market is "pitched", the rest "flat" |
| Existing solar (P.S. 24) | 457,512 kWh a year is from LL84; the **380 kW size is an estimate** (about 1,200 kWh per kW), not public data |
| Existing systems (others) | "none" for Jefferson Market and P.S. 38 (stated choice, not confirmed); blank for Red Hook |
| Budget amount, year, type | **Stated choice** (not public) |
| Critical loads | **Stated choice** (cooling-center use not confirmed) |
| Roof replaced year | Left blank on purpose |

## Two passes on Oct 15, 2026

Real Claude (`claude-sonnet-5-5`) with live PLUTO, footprints, PVWatts and EIA.

**First pass**, with roof areas I guessed (floor area divided by floors): all four `done`, Check 4 passed on the first try. The traces exposed the problems below, so we fixed them.

**Second pass**, after the changes, with roof areas from the footprint suggestion:

| Case | Status | Check 4 | Tool calls | Time | What happened |
| --- | --- | --- | --- | --- | --- |
| Jefferson Market | partial, by design | passed | 8 | 82 s | The roof is pitched, so the roof formulas refused. No solar size, output or savings; scenarios B and C not costed; the plan tells the user to have an engineer or roofer verify the usable area and re-plan; scenario A costed |
| Red Hook Rec | done | passed first try | 17 | 129 s | Asks once about existing systems; says the LPC gives an advisory report, not a permit; scenario C reaches the goal but costs $918k-$1.88M more than the budget, stated with "whether to extend it is your decision" |
| P.S. 38 | done | passed first try | 16 | 108 s | With the realistic 34,360 sq ft roof, scenario C is capped at 100% of use; surplus of 96-158k kWh a year reported and not counted as savings; $1.39M-$2.54M over budget stated |
| P.S. 24 | partial | rejected twice (false positive) | 10 | 120 s | The existing 380 kW array already fills the usable roof, so the plan costs efficiency only and asks to verify free roof. Check 4 rejected it for treating the user's own existing-array kWh as an invented solar figure. That bug is fixed and the stored plan now re-checks as passing |

## What the first pass exposed, and what changed

| Problem in the first pass | Fix |
| --- | --- |
| The financial model had no ceiling: P.S. 38's scenario C claimed a 205-234% reduction | No reduction above 100% of use; the surplus is reported as potential and never counted as savings; every scenario that costs more than the budget states the gap in dollars and that extending the budget is the user's decision |
| No input for existing solar: P.S. 24 was planned as if its roof were empty | Intake section for existing solar, other renewables and efficiency work; new arrays sized only on the free roof; a blank section makes the plan ask once |
| A pitched roof was sized like a flat one (55 kW) | Roof type pick-list; any roof that is not flat is refused until an engineer or roofer verifies the usable area |
| My roof areas were guesses; P.S. 38's was about 60% too high (55,000 vs 34,360 sq ft) | The form suggests a roof area from building footprints; a typed roof area far from the outlines is flagged; every plan says to verify the roof area |
| The footprint dataset's `shape_area` column looked like square meters | It is neither square feet nor square meters (a constant 1/6.15 of the true area); areas are computed from the outline geometry |
| The plan said "LPC permit" for a landmark on parkland | Check 4 requires "advisory report" when the building is both a landmark and on parkland |
| Cited calculations were never checked against what the run produced | A cited `calc_id` must be one the run made, and a sentence about scenario B must cite F-B |
| Flood rule read only FEMA's effective map | Unchanged on purpose: only the current effective map is used, and past flooding is not read from other maps |

## Still open

- Tariff, incentives and battery sizing are still case 1's samples in these runs (the folders now hold the real FEMA flood zone only).
- The roof areas come from outlines; a lot can hold buildings that are not the user's (Red Hook has four).
- For a pitched roof with a verified area, solar output still uses the flat-roof tilt and direction (flagged `pitched_roof_output_not_modeled`).
- The 380 kW existing array at P.S. 24 is an estimate, so its "no free roof" conclusion rests on it.
- A pitched-roof plan returns `partial` because the solar tool counts as a failed tool; a dedicated status for "waiting on a verification" may read better.

## Sources

- NYC Open Data: LL84 2023-present (`5zyy-y8am`), PLUTO (`64uk-42ks`), building footprints (`5zhs-2jue`)
- FEMA National Flood Hazard Layer: https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer
- LPC designation report LP-2241, Red Hook Play Center: https://s-media.nyc.gov/agencies/lpc/lp/2241.pdf
- Jefferson Market Library: https://en.wikipedia.org/wiki/Jefferson_Market_Library
- Red Hook Recreation Center Sandy damage: https://therealdeal.com/2012/12/24/badly-damaged-red-hook-rec-center-reopens/ and https://www.brooklynpaper.com/stories/42/19/dtg-8-million-red-hook-rec-center-investment-2019-05-10-bk.html
