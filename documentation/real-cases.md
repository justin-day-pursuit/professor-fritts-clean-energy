# Real-building test cases

Four real NYC public buildings, added Oct 15, 2026, to test Professor Fritts on real addresses and public data instead of fictional buildings. Each has a folder under `backend/mocks/fixtures/` holding:

- `intake.json`: public data where it exists; the rest are stated choices (see below)
- `live/`: what the live tools returned on Oct 15, 2026 (PLUTO, PVWatts, EIA)
- `live_run_2026-10-15.md`: the roadmap Claude wrote in that live run
- `get_hazard_context.json`: the real FEMA effective flood zone for the site (looked up by hand); heat and storm ratings were not looked up
- `get_utility_tariff.json`, `search_ny_incentives_and_rules.json`, `optimize_solar_storage.json`: copies of case 1's samples, because these tools have no live version yet

They are **not** eval cases yet (no `expected.json`, no scripted run). Run one live from `backend/`:

```bash
TOOL_MODE=live python manage.py run_case --case real2_red_hook_rec_center --llm anthropic --message "<the question in intake.json>"
```

## The buildings

| Folder | Building | BBL | What it tests |
| --- | --- | --- | --- |
| `real1_jefferson_market_library` | Jefferson Market Library (NYPL), 425 6th Ave, Manhattan | 1006060001 | Historic district (LPC review), a pitched 1877 roof with a clock tower |
| `real2_red_hook_rec_center` | Red Hook Recreation Center (NYC Parks), 155 Bay St, Brooklyn | 3005820001 | Parkland, individual landmark (Red Hook Play Center, LP-2241, 2008), basement flooded in Hurricane Sandy while FEMA's effective map says shaded X |
| `real3_ps38_staten_island` | P.S. 38 (R038), 421 Lincoln Ave, Staten Island | 5037320006 | A typical school; PLUTO disagrees with LL84 on floor area |
| `real4_ps24_bronx_existing_solar` | P.S. 24 (X024), 660 W 236th St, Bronx | 2059170140 | A roof that already has solar (457,512 kWh made in 2024); the intake has no field for it |

## Where the inputs come from

| Input | Source |
| --- | --- |
| Annual kWh | LL84 2024, grid electricity purchased (NYC Open Data `5zyy-y8am`) |
| Floor area, year built | LL84 2024 (PLUTO is checked against them during the run) |
| Landmark, historic district, owner | PLUTO (`64uk-42ks`) |
| Flood zone | FEMA National Flood Hazard Layer, effective map |
| Roof area | **Estimate**: floor area divided by PLUTO floors, checked against building footprints (`5zhs-2jue`, whose `shape_area` appears to be square meters). Verify on aerial imagery. |
| Roof type | **Estimate** from aerial imagery |
| Budget amount, year, type | **Stated choice** (not public) |
| Critical loads | **Stated choice** (cooling-center use not confirmed) |
| Roof replaced year | Left blank on purpose |

## Live results, Oct 15, 2026

Real Claude (`claude-sonnet-5-5`) with live PLUTO, PVWatts and EIA.

| Case | Status | Check 4 | Tool calls | Time | Solar estimate (PVWatts) |
| --- | --- | --- | --- | --- | --- |
| Jefferson Market | done | passed first try | 16 | 123 s | 55 kW, 66,286-72,833 kWh/yr |
| Red Hook Rec | done | passed first try | 16 | 121 s | 180 kW, 215,488-236,764 kWh/yr |
| P.S. 38 | done | passed first try | 17 | 101 s | 458 kW, 541,272-594,828 kWh/yr |
| P.S. 24 | done | passed first try | 17 | 115 s | 317 kW, 377,102-414,398 kWh/yr |

## Trace review

**What worked.** The model caught every data problem we planted or that the real data contained, and said so in the plan instead of hiding it:

- Jefferson Market: the live record set the landmark flag from the historic district, and the plan required an LPC review, warned that a pitched roof and clock tower may fit less than 55 kW, and kept efficiency-only as the fallback if LPC says no.
- Red Hook: it noticed the hazard sample described a Queens site in zone X, said it did not trust it given the Sandy flooding, and planned flood protection (equipment above the design flood elevation) and an Appendix G review anyway. It required both the LPC review and a parkland review by counsel, and said scenario B gives no backup power for the cooling center.
- P.S. 38: it flagged the PLUTO floor area (17,620 sq ft, one floor) against the intake (55,860), and said that if the city is right, the 55,000 sq ft roof is not plausible and the solar figures are overstated.
- P.S. 24: it worked out that the new array would double-count the existing one, refused to rely on the scenario C numbers, and asked for the existing array size and how its output is credited.

**Problems the traces exposed** (not fixed yet):

1. **The financial model has no ceiling at 100% of use.** P.S. 38's scenario C reports a 205-234% reduction and P.S. 24's 181-208%, and both are marked as reaching the goal. Solar beyond annual use is valued at the retail rate. The tool should cap the credited solar at annual use (or model export separately) and flag it.
2. **No input for existing solar.** P.S. 24 was planned as if its roof were empty. The intake needs an existing-solar field (kW and kWh/yr), and C1 and PVWatts need to size only the free roof.
3. **Solar sizing ignores roof type.** C1 and PVWatts assume a flat roof at 10° tilt, so the pitched landmark roof got the same 55 kW as a flat roof would. The plan caveated it, but the tool should not size a pitched or tower roof the same way.
4. **Sample tools describe the wrong site.** In these runs the tariff, incentives, hazard and battery data came from case 1 (a Queens site, retrieved 2025-10-01, stale). The repo folders now carry the real FEMA zone, but incentives and battery sizing are still case 1's samples.
5. **The flood rule only reads FEMA's effective zone.** Red Hook is shaded X on the effective map but flooded in Sandy. The model handled it because the user mentioned Sandy; Check 4 would not have required it. NYC's code uses the more restrictive of the effective and 2015 preliminary maps, so the hazard tool should read both.
6. **Our roof-area estimates drive the answer.** P.S. 38's 458 kW array comes from the 55,000 sq ft roof we entered. Roof area is the most important input to verify before trusting any solar or scenario number.
7. Small: on city parkland LPC issues an advisory report, not a permit, but the plan says "LPC permit review" (Check 4 accepts either). The plan also sometimes cites `F-A` for the solar-alone figure, which comes from `F-B`.

## Sources

- NYC Open Data: LL84 2023-present (`5zyy-y8am`), PLUTO (`64uk-42ks`), building footprints (`5zhs-2jue`)
- FEMA National Flood Hazard Layer: https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer
- LPC designation report LP-2241, Red Hook Play Center: https://s-media.nyc.gov/agencies/lpc/lp/2241.pdf
- Jefferson Market Library: https://en.wikipedia.org/wiki/Jefferson_Market_Library
- Red Hook Recreation Center Sandy damage: https://therealdeal.com/2012/12/24/badly-damaged-red-hook-rec-center-reopens/ and https://www.brooklynpaper.com/stories/42/19/dtg-8-million-red-hook-rec-center-investment-2019-05-10-bk.html
