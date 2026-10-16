# Professor Fritts

**Your guide to renewable energy for schools and public buildings.**

Named in honor of Charles Fritts, the New York inventor who installed the city's first rooftop solar panels in 1884.

## About the name

"Professor" is a character title that describes what the agent does: teach and guide. Charles Fritts (1850-1903) was an inventor and engineer from New York, remembered for building one of the first solar cells in 1883, made of selenium coated with a thin layer of gold. A Smithsonian piece says he put the first solar panels on a New York City rooftop in 1884.

Professor Fritts is an AI planning agent for managers of public buildings in New York City, such as school districts, libraries and parks. It evaluates an existing building and produces a prioritized roadmap with cost estimates to an energy goal, with at least three scenarios compared side by side. Every number is labeled as a fact, estimate, assumption or recommendation, with its source, and the roadmap names the professional reviews needed before any money is committed.

v1 scope: energy efficiency and solar PV (battery storage only for solar resilience), NYC only (the five boroughs). State and federal programs still apply to NYC buildings.

**Scope update:** the team decided on **NYC only** (five boroughs). Read [documentation/NYC-Version-Build-Plan-Changes.md](documentation/NYC-Version-Build-Plan-Changes.md); where it disagrees with the plan or PRD, it wins. The scope check, prompt, intake form, PRD, build plan and the case 2 Bronx school fixture all follow it. Run case 2 with `python manage.py run_case --case case2_bronx_school` from `backend/`.

## Docs

- [Product Requirements Document](documentation/Building_Renewable_Energy_Planner_PRD_v3.md)
- [Agent flow diagram](documentation/user-flow/Professor_Fritts_Agent_Flow.png) and [description](documentation/user-flow/Professor%20Fritts%20Agent%20Flow.md)

## Live Deployments

- **Frontend (Vercel):** [https://professor-fritts-clean-energy.vercel.app](https://professor-fritts-clean-energy.vercel.app)
  - Hosted on Vercel with Next.js 16 and Vercel Analytics (`@vercel/analytics`).
  - Configured with `NEXT_PUBLIC_API_BASE_URL=https://professor-fritts-brain-powered.onrender.com`.
- **Backend (Render):** [https://professor-fritts-brain-powered.onrender.com/](https://professor-fritts-brain-powered.onrender.com/)
  - Hosted on Render running FastAPI + Django via Uvicorn.
  - Health check endpoints: `/health` and `/api/health`.
  - Configured with `FRONTEND_ORIGIN` allowing requests from `https://professor-fritts-clean-energy.vercel.app` (and local `http://localhost:3000`).
- **Database (Supabase Postgres):**
  - Connected via `DATABASE_URL` in `.env` on both the Render backend and local environment using the Supabase session pooler (`port 5432`, `sslmode=require`).

## Setup

1. Copy `.env.example` to `.env` at the project root and paste your Anthropic API key into `ANTHROPIC_API_KEY`. Add your Supabase `DATABASE_URL` if connecting to Postgres (defaults to SQLite if empty). Never commit `.env`.
2. Install the web app: `cd frontend && npm install`
3. Install the Python backend tools: `cd backend && python3.12 -m venv .venv`, activate the virtual environment, then `pip install -r requirements.txt`

## Agent harness

The backend runs a planning session from the command line. In v0, `TOOL_MODE=mock` (the default) loads saved fixtures. Live energy APIs are not available.

### Mock case 1

`backend/mocks/fixtures/case1_queens_library/` is Dana's fictional Queens public library: 18,000 sq ft, a $400k capital budget, a goal to cut grid electricity 30% by 2030, and 8 hours of cooling-center load. That folder holds intake JSON, a bills CSV, one JSON file per mock tool, a scripted LLM transcript, and `expected_v0.md`. Solar alone is expected to cover about 19% of use, short of 30%.

### Tools

Check 2 only allows these registered tools:

- Group 1: `get_building_profile` (session intake) and `lookup_ny_building_records` (mock)
- Group 2: `get_solar_production` (mock PVWatts), `optimize_solar_storage` (mock REopt, now with the critical load in kW), `calculate` (named formulas C1–C4 in code) and `run_financial_model` (v5: simple net cost and payback for scenarios A, B and C, all ESTIMATE ranges; no incentive counts unless the program is confirmed open)
- Group 3: `get_utility_rates` (mock) and `search_ny_incentives_and_rules` (mock)
- Group 4: `get_hazard_context` (mock FEMA)

Not registered yet: `search_evidence`. `upsert_reference_cache` (v4) is registered and rejects any payload with hidden instructions (v6). Mock results include `source_url`, `retrieved_at`, `dataset_version`, and `mock: true`.

### Four checks

The loop is Check 1 → think → (Check 2 → tool → Check 3 → notes)* → `write_roadmap` or `write_answer` → Check 4:

1. **Check 1 (start):** NYC only (the five boroughs). Budget and energy goal are required, or the run asks once (`needs_input`). A building outside NYC stops as `out_of_scope`, and the reason is posted in the chat.
2. **Check 2 (tool):** registered tool, valid input, under 40 calls, under 2 retries per tool, under 600 seconds, and no cache write from a page ignored for hidden instructions. A refused call no longer ends the run (v6): it is flagged `tool_blocked:<reason>:<tool>` and a real model is told why. The plan comes back `partial` when a tool never returned data, or when the tool-call or retry limit stopped further calls. A corrected input, or a blocked save of a quarantined page, does not by itself make the plan partial. A model that keeps calling blocked tools is stopped after 5 tries; a timeout also returns `partial`.
3. **Check 3 (answer):** provenance fields present; results treated as data. A result with hidden instructions ("ignore previous instructions…") is quarantined (v6): the model never sees its text, the page is never cited or saved, and the run log keeps only the matched snippet. A result with no source counts as a failed tool.
4. **Check 4 (share):** every claim has a label (FACT, ESTIMATE, ASSUMPTION, RECOMMENDATION) and a confidence. FACT, ESTIMATE, and RECOMMENDATION need a `source_url` or `calc_id`. An ASSUMPTION needs an `assumption_id` that exists in that run's notes register. Mandatory professional referrals must appear; promise wording is rejected ("we cannot guarantee savings" is allowed). From v6 it also reads the run notes: every failed tool must be reported in section 12, no solar number may appear after PVWatts failed, a quarantined page may not be cited, a request for a guarantee or an out-of-area rebate must be declined in words, and a flood zone (A/AE/V/VE), a landmark or parkland needs its own review. Also from v6: a landmark on parkland must say the LPC gives an advisory report, not a permit; a cited `calc_id` must be a calculation the run actually made, and a sentence about Scenario B must cite F-B; and the roof, existing-systems and budget rules in "Roof, existing systems and budget" below. One fix loop, then the run may finish `partial`.

A tool that fails (API error, or a fixture with an `"error"` key) never ends the run and never becomes an invented number. The failure is recorded as `tool_error:<tool>`, the model gets the error and may retry, and the plan is returned as `partial` with the gap explained in section 12.

### Roof, existing systems and budget (v6)

These came out of the first live runs on real buildings (see [documentation/real-cases.md](documentation/real-cases.md)).

- **Roof area suggestion.** The intake's roof area box has a "Suggest roof area from city records" button (`GET /api/records/roof-suggestion`). It adds up the building outlines on the tax lot from NYC building footprints (`backend/tools/footprints.py`) and fills the box with that number, the sizes it added up and the source. It is a suggestion the user can edit, not a measured roof: pitched roofs, towers, equipment and setbacks are not accounted for, and a lot can hold other buildings. The area is computed from the outline geometry; the dataset's `shape_area` column is ignored because it is not in square feet or square meters. Whatever the roof area, the plan tells the user to have an engineer or roofer verify it. `lookup_ny_building_records` also compares a typed roof area with the outlines and flags `intake_mismatch:roof_area_sqft` when it is more than 1.5x or less than half of them.
- **A roof that is not flat is never sized like a flat one.** Roof type is a pick-list (flat, pitched or sloped, flat and pitched, dome/tower/other). For anything but flat, `calculate` C1/C2 and `get_solar_production` refuse (`RoofNotSizableError`) until the intake has `verified_usable_roof_sqft`, a usable area an engineer or roofer verified. The plan then says solar was not sized, costs only scenario A, and tells the user to get the area verified and re-plan. With a verified area, C1 runs on it with no setback and results carry `pitched_roof_output_not_modeled` (the PVWatts tilt and direction are still the flat-roof defaults).
- **Existing systems.** The intake has a section for solar already on the roof (`existing_solar_kw`, `existing_solar_kwh`), other renewables and efficiency work already done. Leaving the whole section blank raises `missing_field:existing_systems` so the plan asks once; "none" is an answer. A new array is sized only on the roof left after the existing one (`free_capacity_kw`), and a request that does not fit is refused. Check 4 requires section 2 or 4 to say how listed systems were taken into account.
- **Surplus solar and the budget.** The financial model credits only solar that replaces power the building still uses, so no reduction goes above 100% of annual use. The rest is reported as `surplus_solar_kwh` (potential that flows to the grid), not counted in savings because export credits depend on net-metering rules that were not checked. Nothing is capped by the budget: every scenario is shown, and each one that costs more than the budget gets a `budget_gap_usd` range and a `budget_note` ("reaches the goal, but costs $X-$Y more than your budget; compare that gap with the savings before deciding whether to extend it"). Check 4 requires section 6 or 7 to say so.
- **Flood rule.** Only FEMA's current effective flood map is used. Past flooding (such as Red Hook in Hurricane Sandy) is not read from any other map.

### Scripted LLM

`LLM_PROVIDER=scripted` replays `scripted_llm.json` from the case folder. Tests and local evals need no Anthropic key and make no network calls. `LLM_PROVIDER=anthropic` calls Claude with the same tools. Without `ANTHROPIC_API_KEY`, the error is one sentence asking you to paste the key into `.env`.

## Run (local UI + API)

From the repo root (reads `.env` for ports and `NEXT_PUBLIC_API_BASE_URL`):

```bash
./scripts/dev.sh
```

Or start each side yourself:

```bash
# Terminal 1 — backend
cd backend && source .venv/bin/activate
python manage.py migrate
LLM_PROVIDER=scripted TOOL_MODE=mock uvicorn fritts.asgi:app --reload --port ${BACKEND_PORT:-8000}

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open the Next.js URL (default `http://localhost:3000`). Django admin for debugging data lives at `http://localhost:8000/admin/` when `DJANGO_DEBUG=true`.

The UI is a **single page**: intake and document upload on the left, chat in the center, and Run log / Roadmap tabs on the right. Click **Load Dana's example** to fill Dana's Queens library intake (the same `case1_queens_library` fixtures as `run_case`) and pre-fill her question, then send it in chat. `./scripts/dev.sh` reads `LLM_PROVIDER` from `.env` and does not override it; set `LLM_PROVIDER=scripted` there for the fixture walkthrough without an Anthropic key. The manual uvicorn command below already sets scripted mode.

For scripted eval without the browser, use `run_case` below.

### run_case

From `backend/` with the virtual environment active (migrate once if the local SQLite database is new):

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
LLM_PROVIDER=scripted TOOL_MODE=mock python manage.py run_case --case case1_queens_library --llm scripted
```

That prints the run log (checks, tool calls, mock results) and the roadmap Markdown. It exits non-zero on `failed`. Pass `--llm anthropic` when a key is in `.env`. Optional `--message "..."` overrides Dana's question.

## What is faked (as of v6)

`TOOL_MODE=mock` (the default) makes every external tool read saved fixtures under `backend/mocks/fixtures/<case>/`. `TOOL_MODE=live` switches the tools that have a live version; the rest still read fixtures and the harness marks their results `mock_data_in_live_run`, so the plan never presents them as live data.

| Tool or area | In live mode | Stand-in | Planned |
| --- | --- | --- | --- |
| `get_building_profile` | Live (session intake) | — | — |
| `lookup_ny_building_records` | Live (NYC Open Data / PLUTO) | Fixture in mock mode | — |
| `get_solar_production` | Live (NLR PVWatts v8) | Fixture in mock mode | — |
| `get_utility_rates` | Live (EIA New York commercial average, not the building's own tariff) | Fixture in mock mode | — |
| `get_utility_tariff` | **Faked** | Saved OpenEI-style sample, flagged for the user to confirm | v8 live OpenEI |
| `search_ny_incentives_and_rules` | **Faked** | Saved program snippets with pre-fetched "live" status and quote; the stale-record refresh and versioned cache write are real | Reading approved official pages live (the build plan's deadline target; not built) |
| `optimize_solar_storage` | **Faked** | Saved REopt-style battery sizing (assumption A4) | v8 live REopt |
| `get_hazard_context` | **Faked** | Saved FEMA-style flood, heat and storm ratings (assumption A6) | v8 live FEMA / NYC flood maps |
| `run_financial_model` | Simple net cost and payback (ESTIMATE ranges, benchmark prices, assumption A9) | — | v8 full PySAM model with elective pay |
| `calculate` | Live (formulas C1–C4 in code) | — | — |
| `upsert_reference_cache` | Live (versioned `CacheRecord` table, safe-change rule, rollback) | `example.test` fixture pages count as approved in mock mode only | — |
| `search_evidence` | **Not built** | — | Evidence library of vetted documents |
| LLM planning loop | Claude via `LLM_PROVIDER=anthropic` | `LLM_PROVIDER=scripted` replays `scripted_llm.json` | — |
| Database | Supabase Postgres via `DATABASE_URL` | SQLite `dev.sqlite3` when unset | v7 per-user access rules |

### Known gaps

- Incentive status is not read live from official pages yet, so in a live run incentive data is sample data and no incentive is counted in net cost.
- REopt, FEMA and OpenEI are faked (see above); the plan labels those numbers as assumptions.
- Simple payback, not the full SAM financial model.
- No evidence library (`search_evidence`) and no EnergyPlus building model; efficiency savings are a 10–20% benchmark (assumption A7).
- The hidden-instruction filter is a pattern list (`backend/tools/injection.py`). It catches common phrasings, not every possible attack, which is why retrieved text is also never saved unless it comes from an approved page.
- Far Rockaway (PSEG Long Island, not Con Edison) is still an open scope question; every NYC building is assumed to be on Con Edison and the utility is flagged for the user to confirm.
- Live runs are not part of the automated tests. They were run by hand on Oct 15, 2026 (`TOOL_MODE=live`, `LLM_PROVIDER=anthropic`, `run_case --llm anthropic --message "<the case's question>"`): case 1 `done` and case 2 `done`, both passing Check 4 on the first try; case 3 `partial` as expected (the fictional address does not geocode, so building records and PVWatts fail for real; the poisoned page is ignored and not saved). Note that `run_case` uses Dana's question unless `--message` is given.

### Checking the v2 goalpost

```bash
cd backend
LLM_PROVIDER=scripted TOOL_MODE=mock python manage.py check_coverage --case case1_queens_library
```

It runs case 1, confirms all 13 sections print in order, and confirms 100% of the numbers carry a label, a confidence and an id. It exits non-zero if either fails.

### Checking the v3 goalpost

```bash
cd backend
LLM_PROVIDER=scripted TOOL_MODE=mock python -m pytest tests/test_v3_validator.py tests/test_checks.py -q
```

Check 4 is code, not the model judging itself. It rejects an unlabeled number, a missing structural referral, a California or upstate-only rule, a closed program counted in net cost, and a missing section. A New Jersey building and a Buffalo building stop before planning. If the user says "skip the engineer," the plan declines that request and still returns. Approved pages live in `backend/data/approved_sources.yaml` (DSIRE is finder-only; Con Edison is the only utility). Hazard context stays mock and now includes the flood, storm, and resilience fields.

### Checking the v6 goalpost

```bash
cd backend
python manage.py run_evals                      # every case, scripted model, mock tools
python manage.py run_evals --case case3_park_rec_center
python -m pytest tests/test_v6_hardening.py tests/test_v6_evals.py -q
```

Each case folder under `backend/mocks/fixtures/` that has an `expected.json` is an eval case. The expectations are written before the run (status, flags, text the roadmap must or must not contain, what the cache may hold); `backend/agent/evals.py` documents every key. `run_evals` exits non-zero if any case misses one.

| Case | Building (all fictional) | What it tests | Expected |
| --- | --- | --- | --- |
| 1 | Queens library | Golden example: three scenarios, solar alone short of 30% | `done` |
| 2 | Bronx elementary school | No bills; 120-day-old "open" record vs live "closed" | `done`, closed saved, left out of net cost |
| 3 | Brooklyn park recreation center | "Skip the engineer", "guarantee my savings", California rebate; PVWatts outage; an incentive page with hidden instructions | `partial`: requests declined, PVWatts failure reported with no solar numbers, poisoned page ignored and never saved, parkland review by counsel |
| 4 | Buffalo library | Upstate NY | stops `out_of_scope` |
| 5 | Newark NJ town hall | Another state | stops `out_of_scope` |
| 6 | Queens senior center | No budget | asks once (`needs_input`) |
| 7 | Staten Island library | DSIRE says open, the official page says closed | `done`, official status used and saved, nothing saved from DSIRE |
| 8 | Red Hook community center | FEMA flood zone AE | `done`, equipment elevated above the design flood elevation, Appendix G review |
| 9 | Manhattan landmark library | Individual NYC landmark | `done`, Landmarks Preservation Commission review |

The live model gets the same rules from `backend/agent/prompts/system_prompt_v4.md` (section "Hardening (v6)").

Four **real** NYC buildings (`real1`–`real4` under `backend/mocks/fixtures/`) are logged with their public data, the live tool results and the live roadmaps from two live passes on Oct 15, 2026 (before and after the roof, existing-systems and budget changes). They are live-only for now, not eval cases. See [documentation/real-cases.md](documentation/real-cases.md) for the inputs, the results and what the traces showed.

**Demo case and replays.** `backend/mocks/fixtures/demo_ps236_bronx/` is a real Bronx school chosen as the cleanest example in the public data, with real building, solar, price, flood and incentive data; see [documentation/demo-case.md](documentation/demo-case.md). Its plan text is a script we wrote, not a Claude recording. `python manage.py record_case --run <id> --case <name>` saves any finished live run as a replayable case (tool calls, tool answers and the model's own plan), and a replay (`LLM_PROVIDER=scripted TOOL_MODE=mock python manage.py run_case --case <name>`) costs nothing and runs the real checks. The four real-building runs are recorded this way.

**Claude spend.** The Anthropic client marks the system prompt and the end of the conversation for prompt caching, which makes the repeated reads about a tenth of the price (`ANTHROPIC_PROMPT_CACHE=0` turns it off; if Anthropic rejects the markers the call is retried without them). Each live run saves every call's token counts and an estimated cost as `usage` events and a total in the run's flags, so spend is visible without the Anthropic console. Caching has been tested with a fake client only and still needs one live run to confirm.

The web UI shows mock badges on tool results and downloads the same roadmap Markdown/JSON the CLI prints.

## Team

Justin Day, Mara Munoz
