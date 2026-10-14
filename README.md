# Professor Fritts

**Your guide to renewable energy for schools and public buildings.**

Named in honor of Charles Fritts, the New York inventor who installed the city's first rooftop solar panels in 1884.

## About the name

"Professor" is a character title that describes what the agent does: teach and guide. Charles Fritts (1850-1903) was an inventor and engineer from New York, remembered for building one of the first solar cells in 1883, made of selenium coated with a thin layer of gold. A Smithsonian piece says he put the first solar panels on a New York City rooftop in 1884.

Professor Fritts is an AI planning agent for managers of public buildings in New York State, such as school districts, libraries and parks. It evaluates an existing building and produces a prioritized roadmap with cost estimates to an energy goal, with at least three scenarios compared side by side. Every number is labeled as a fact, estimate, assumption or recommendation, with its source, and the roadmap names the professional reviews needed before any money is committed.

v1 scope: energy efficiency and solar PV (battery storage only for solar resilience), New York State and NYC only.

## Docs

- [Product Requirements Document](Building_Renewable_Energy_Planner_PRD_v3.md)
- [Agent flow diagram](user-flow/Professor_Fritts_Agent_Flow.png) and [description](user-flow/Professor%20Fritts%20Agent%20Flow.md)

## Setup

1. Copy `.env.example` to `.env` at the project root and paste your Anthropic API key into `ANTHROPIC_API_KEY`. Never commit `.env`.
2. Install the web app: `cd frontend && npm install`
3. Install the Python backend tools: `cd backend && python3.12 -m venv .venv`, activate the virtual environment, then `pip install -r requirements.txt`

## Agent harness

The backend runs a planning session from the command line. In v0, `TOOL_MODE=mock` (the default) loads saved fixtures. Live energy APIs are not available.

### Mock case 1

`backend/mocks/fixtures/case1_queens_library/` is Dana's fictional Queens public library: 18,000 sq ft, a $400k capital budget, a goal to cut grid electricity 30% by 2030, and 8 hours of cooling-center load. That folder holds intake JSON, a bills CSV, one JSON file per mock tool, a scripted LLM transcript, and `expected_v0.md`. Solar alone is expected to cover about 19% of use, short of 30%.

### Tools

Check 2 only allows these registered tools:

- Group 1: `get_building_profile` (session intake) and `lookup_ny_building_records` (mock)
- Group 2: `get_solar_production` (mock PVWatts), `optimize_solar_storage` (mock REopt), and `calculate` (named formulas C1–C4 in code)
- Group 3: `get_utility_rates` (mock) and `search_ny_incentives_and_rules` (mock)
- Group 4: `get_hazard_context` (mock FEMA)

Not registered in v0: `run_financial_model`, `search_evidence`, `upsert_reference_cache`. Mock results include `source_url`, `retrieved_at`, `dataset_version`, and `mock: true`.

### Four checks

The loop is Check 1 → think → (Check 2 → tool → Check 3 → notes)* → `write_roadmap` or `write_answer` → Check 4:

1. **Check 1 (start):** New York only. Budget and energy goal are required, or the run asks once (`needs_input`). Out-of-state buildings stop as `out_of_scope`.
2. **Check 2 (tool):** registered tool, valid input, under 40 calls, under 2 retries per tool, under 600 seconds.
3. **Check 3 (answer):** provenance fields present; hidden-instruction patterns flagged; results treated as data.
4. **Check 4 (share):** every claim has a label (FACT, ESTIMATE, ASSUMPTION, RECOMMENDATION) and a confidence. FACT, ESTIMATE, and RECOMMENDATION need a `source_url` or `calc_id`. An ASSUMPTION needs an `assumption_id` that exists in that run's notes register. Mandatory professional referrals must appear; promise wording is rejected. One fix loop, then the run may finish `partial`.

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

## What is faked in v0

| Area | v0 stand-in | Later owner |
| --- | --- | --- |
| External tools (PVWatts, REopt, rates, incentives, FEMA, NY building records) | `TOOL_MODE=mock` JSON fixtures under `backend/mocks/fixtures/` | Live API integration block |
| LLM planning loop | `LLM_PROVIDER=scripted` replays `scripted_llm.json`; optional Anthropic when keyed | Production LLM + eval harness |
| Tool result cache | In-memory / JSON file cache in the backend | Supabase-backed reference cache |
| Database | SQLite via Django (local `.data/`) | Supabase Postgres |
| Roadmap sections | PRD sections 1,2,3,5,6,8,9,10,12,13 only; footer notes missing 4, 7, 11 | v2 / v5 product blocks |
| Financial model, evidence search | Tools not registered in v0 | Future tool units |

The web UI shows mock badges on tool results and downloads the same roadmap Markdown/JSON the CLI prints.

## Team

Justin Day, Mara Munoz
