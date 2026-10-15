# Building Renewable Energy Planner — Build Plan

Oct 13, 2026 · @m

## How to use this plan

The build runs in seven blocks, v0 to v6, and v6 is the deadline target: an agent that runs all eval cases end-to-end and returns a labeled, sourced roadmap. Each block adds one capability on top of the last and ends in a goalpost. Do not start the next block until the current goalpost passes.

- **Team:** two builders. Builder A owns the "hands" (tools and data). Builder B owns the "brain" (agent, rule checker and tests).
- **Deadline scope:** some tools run live, the rest return saved test data ("mock mode"). Everything faked is listed in the Reference table and the README.
- **Language:** Python, because PySAM and most energy tooling are Python.
- **Rule of thumb:** if a block slips, cut scope inside the block, never skip its goalpost.

## Before you start

Finish this checklist before writing agent code; it takes about half a day and removes most of the blockers.

### Decisions to lock

- [ ] One product name: "Professor Fritts" (persona) or "Building Renewable Energy Planner" (product), used the same way in the prompt, flowchart and README
- [ ] Scope is NYC only (the five boroughs); New York State and federal programs still apply to NYC buildings (decided Oct 15, 2026; see NYC-Version-Build-Plan-Changes.md)
- [ ] Label words: FACT, ESTIMATE, ASSUMPTION, RECOMMENDATION everywhere (the flowchart's "guess" becomes ASSUMPTION)
- [ ] Cache scope: one shared cache for all users, with add-only versioned writes
- [ ] Tool-call limit per request (suggested start: 40 calls, 2 retries per tool, 10-minute total timeout)
- [ ] Deadline definition of done: all eval cases pass in mock mode and case 1 runs with live data

### Accounts and keys

- [ ] NLR developer key (covers PVWatts and REopt): developer.nlr.gov/signup
- [ ] OpenEI key (utility tariffs): openei.org/services/api/signup
- [ ] EIA key (electricity prices): eia.gov/opendata/register.php
- [ ] NYC Open Data app token (free account on data.cityofnewyork.us; data.ny.gov is no longer needed)
- [ ] Anthropic API key (the agent itself)
- [ ] Email dsire-admin@ncsu.edu asking whether light automated reading of the public DSIRE site is allowed, and for API pricing

### Environment

- [ ] Python 3.11+, with pinned versions of the Anthropic SDK, requests, PyYAML and pytest
- [ ] PySAM installed and its version pinned (needed later, in v5 or after the deadline)
- [ ] SQLite for the cache (no setup; the database is a single file)
- [ ] Shared password manager or secrets store for keys; never paste keys into chat or code

### Repo

- [ ] Create the repo with the folder layout below, a README, `.env.example` and `.gitignore` (ignore `.env` and `cache.db`)
- [ ] Protect `main`: changes only by pull request, reviewed by the other builder

```
energy-planner/
  agent/       system_prompt.md, orchestrator.py, output_schema.py
  tools/       schemas.py + one file per tool
  validator/   check_output.py
  data/        approved_sources.yaml, evidence/, cache.db (ignored)
  evals/       fixtures/, cases/, run_evals.py
```

### The contract (both builders, together)

- [ ] Write `tools/schemas.py`: every tool's inputs and outputs, and every output carries `source_url`, `retrieved_at` and `dataset_version`
- [ ] Write the claims format: each number has a value range, units, label, confidence and a source or calculation ID
- [ ] Agree on mock mode: one setting switches every tool between live calls and saved files in `evals/fixtures/`
- [ ] Freeze the contract; change it only after both builders agree

## Build blocks

Each block is a working version of the agent; v0 and v1 land on day 1, v2 and v3 on day 2, v4 and v5 on day 3, and v6 on the last day.

&#91;embedded content: build roadmap · 7 blocks, each with its goalpost\]

Read top to bottom: each box is a working version of the agent, and its right side is the goalpost to pass before the next block starts.

### v0 — Skeleton (day 1)

**Goal:** the agent loop runs end-to-end on fake data, before any real tool exists.

- **Builder A:** repo skeleton, mock-mode switch, fixture files for eval case 1 (Queens library)
- **Builder B:** orchestrator loop (Claude plus tool calls), system prompt v0 loaded from file, run log written for every request

**Goalpost:**

- [ ] Running case 1 in mock mode returns an answer
- [ ] The run log shows at least 3 tool calls and their mock responses

### v1 — First live answer (day 1–2)

**Goal:** one real question answered with real data: how much solar, worth how much.

- **Builder A:** live PVWatts, EIA and NYC Open Data tools, each returning source URL and retrieval date; save each live response as a new fixture
- **Builder B:** a small `calculate` tool so every formula is computed by code and logged with an ID (C1 usable roof area, C2 array size, C3 annual kWh, C4 annual savings)

**Goalpost:**

- [ ] Case 1 with live data returns an annual solar kWh range and a dollar savings range
- [ ] Every number carries a source URL or a calculation ID
- [ ] Re-running PVWatts from the logged inputs matches within ±1%

### v2 — Labeled, structured output (day 2)

**Goal:** the plan comes out in the PRD's 13-section format, and every number is labeled.

- **Builder A:** intake form reader (`get_building_profile`) with missing-field flags; OpenEI tariff tool in mock mode
- **Builder B:** claims format (value range, units, label, confidence, source or calculation ID), assumptions register (A1, A2 …), renderer from claims to the 13 sections

**Goalpost:**

- [ ] Case 1 in mock mode returns all 13 sections in order
- [ ] A script confirms 100% of numbers have a label, a confidence and an ID

### v3 — Rule checker and safety rules (day 2)

**Goal:** a code check (not the model judging itself) blocks bad plans before the user sees them.

- **Builder A:** `approved_sources.yaml` (official NYC, New York State, federal and Con Edison pages, plus DSIRE marked as finder-only); FEMA hazard tool in mock mode
- **Builder B:** validator that checks sections, labels, mandatory referrals (structural PE/RA, roof survey, licensed electrician, fire access, interconnection), NYC-only rules and no closed programs in net cost. Failures go back to the agent once, then it returns a partial roadmap. Requests outside NYC (another state, or upstate or suburban New York) stop immediately.

**Goalpost:**

- [ ] The validator catches all 5 planted defects: an unlabeled number, a missing structural referral, a California rule, a closed program in net cost, a missing section
- [ ] A New Jersey building and an upstate New York building (Buffalo) are each stopped as out of scope
- [ ] "Skip the engineer" is declined, and the rest of the plan still returns

### v4 — Incentives and fresh data (day 3)

**Goal:** incentives are checked live on official pages and saved safely.

- **Builder A:** incentives tool that reads approved official pages and extracts status, deadline and eligibility, keeping the exact quoted text and a page hash. SQLite cache with add-only versions, freshness limits (7, 90, 180 and 365 days), rollback, and the safe-change rule: changes that make a plan more cautious save automatically, more favorable changes save as "pending" until a person confirms.
- **Builder B:** prompt rules for stale data and conflicts; eval case 2 (Bronx elementary school) wired up

**Goalpost:**

- [ ] Case 2 passes: the 120-day-old "open" record is refreshed, "closed" is saved as a new version, the program is left out of net cost and the conflict is shown
- [ ] Rolling back one cache record restores the previous version
- [ ] Nothing from user input, model estimates or non-approved pages is saved

### v5 — Scenarios and resilience (day 3)

**Goal:** the full planning output: three costed scenarios and a backup power plan.

- **Builder A:** simple net cost and payback calculation (labeled ESTIMATE; full PySAM comes later); REopt battery sizing in mock mode
- **Builder B:** scenarios A (efficiency only), B (efficiency + solar within budget) and C (full path to goal); resilience section; roadmap phases 0–5

**Goalpost:**

- [ ] Case 1 compares 3 scenarios on share of goal, upfront and net cost, payback, budget strain and outage hours
- [ ] Solar alone is shown at roughly 15–25% of annual use and flagged as not reaching the 30% goal

### v6 — Hardening and full evals (last day = deadline)

**Goal:** the agent survives bad inputs and passes every test.

- **Both builders:** retrieved text passed to the agent as data and any hidden instructions flagged; tool failures produce a partial roadmap with no invented numbers; tool-call limit enforced; 5 extra eval cases (outside NYC (one upstate NY building and one New Jersey building), no budget, DSIRE says open but the official page says closed, a building in a flood zone, a landmark building); README listing what is faked

**Goalpost (definition of done):**

- [ ] All eval cases pass in mock mode
- [ ] Case 3 passes: the poisoned page is ignored and flagged, the PVWatts failure is reported, and nothing is saved from the bad page
- [ ] Case 1 passes with live data
- [ ] The README lists every faked tool and known gap

## After the deadline

These blocks turn the test-ready agent into one that pilot users can rely on.

- **v7 — Hosted and multi-user:** move the cache, building profiles and run logs to a hosted database (Supabase or plain Postgres), turn on per-user access rules, deploy. **Goalpost:** two users each see only their own buildings, and the shared cache keeps its version history.
- **v8 — All tools live:** full PySAM financial model (including elective pay), live REopt, FEMA and OpenEI, DSIRE as a finder if permission or a subscription comes through, an evidence library of 20+ vetted documents with vector search. **Goalpost:** all eval cases pass in live mode, and SAM results re-run within ±1%.
- **v9 — Pilot:** expand to 20–30 eval cases, then run with 3–5 real facilities managers. **Goalpost:** the PRD's success-metric targets (time saved, supported facts, referral recall, usefulness rating).
- **v10 — Phase 2 modeling:** EnergyPlus / OpenStudio building simulation for efficiency savings. **Goalpost:** modeled savings replace benchmark estimates, with the gap between model and bills shown.

## Branches and ownership

Use one short branch per piece of work and merge into `main` at least once a day.

| Block | Builder A branch | Builder B branch |
| --- | --- | --- |
| Setup | `setup/schemas` (shared) | `setup/schemas` (shared) |
| v0 | `tools/mock-mode` | `agent/orchestrator` |
| v1 | `tools/pvwatts`, `tools/eia`, `tools/nyc-records` | `agent/calculate` |
| v2 | `tools/building-profile`, `tools/utility-rates` | `agent/output-schema` |
| v3 | `data/approved-sources`, `tools/hazard` | `validator/rules` |
| v4 | `tools/incentives`, `tools/cache` | `evals/case2` |
| v5 | `tools/financial`, `tools/storage` | `agent/scenarios` |
| v6 | `evals/extra-cases`, `docs/readme` | `agent/hardening` |

- **Reviews:** every pull request is reviewed by the other builder.
- **The contract:** `tools/schemas.py` changes only when both builders agree.
- **Never commit** `.env` or `cache.db`.
- **Daily:** a 10-minute sync to check which goalposts passed and what is blocked.

## Tool reference

Six tools run live at the deadline (utility rates only partly); the rest return saved test data until v8.

| Tool | Data source | Key needed | At deadline | Block | Difficulty |
| --- | --- | --- | --- | --- | --- |
| get\_building\_profile | Your intake form | None (you build it) | Live (files/SQLite) | v2 | Easy |
| lookup\_ny\_building\_records | NYC Open Data | App token (free) | Live | v1 | Easy |
| get\_solar\_production | NLR PVWatts v8 | NLR key (free) | Live | v1 | Easy |
| get\_utility\_rates | OpenEI rates; EIA prices | OpenEI + EIA keys (free) | EIA live, OpenEI mock | v1, v2 | Medium |
| search\_ny\_incentives\_and\_rules | Approved official pages; DSIRE as finder | None for official pages | Live | v4 | Hard |
| run\_financial\_model | Simple payback now; PySAM later | None | Simple calculation | v5 | Medium |
| optimize\_solar\_storage | NLR REopt | NLR key (free) | Mock | v5 | Medium |
| get\_hazard\_context | FEMA Risk Index, FEMA and NYC flood maps | None | Mock | v3 | Medium |
| search\_evidence | Your vetted documents | None (you build it) | 10 docs, keyword search | v6 | Medium |
| upsert\_reference\_cache | Your SQLite database | None (you build it) | Live | v4 | Hard |
| model\_efficiency\_baseline | EnergyPlus / OpenStudio | None | Not built | v10 | Hard |

Sign-up pages: [NLR](https://developer.nlr.gov/signup/), [OpenEI](https://openei.org/services/api/signup/), [EIA](https://www.eia.gov/opendata/register.php), [DSIRE API](https://dsireusa.org/dsire-api/) (paid; optional).

## Risks and known gaps

The incentives tool is the biggest schedule risk; if it slips, ship v4 with a fixed set of pre-fetched pages and keep the freshness logic.

| Risk | Effect | Fallback |
| --- | --- | --- |
| Incentive pages are hard to read reliably | v4 slips; wrong open/closed status | Keep the quoted text with every status; any unclear status is listed as "uncertain" and left out of net cost |
| API rate limits or outages during testing | Evals fail for reasons unrelated to the agent | Run evals in mock mode by default; run live only for case 1 |
| Picking the right utility tariff | Savings wrong by a wide margin | Show the tariff name and effective date; flag it for user confirmation |
| DSIRE permission not granted | No finder source | Official pages on the approved list cover v1; DSIRE is optional |
| Schema changes mid-build | Builders block each other | Freeze `tools/schemas.py`; changes only with both builders' agreement |

**Known gaps at the deadline:** simple payback instead of full SAM; REopt, FEMA and OpenEI faked; SQLite instead of a hosted database; a small evidence library; no EnergyPlus.
