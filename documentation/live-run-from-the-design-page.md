# Running a real analysis from the design page

When a visitor types their own address on the home page (`/`) and presses **Run Professor Fritts**, the page now starts a real analysis with the same agent the classic planner uses. The saved plans on the home page still replay from recordings, free and in seconds, so the demo never waits on Claude.

## What the visitor sees

1. They type an address and confirm the building. The page reads the city's free records (address search, tax lot, energy report, roof assessment, building outline) and fills in what it can: yearly kWh, roof area, roof condition and any solar already installed. Everything is editable.
2. They add what the city cannot know: capital budget, goal, what must keep running in an outage, roof type, and optionally an electric bill.
3. **Run** needs a budget and a goal. If either is blank, Fritts says what is missing and nothing is started.
4. A progress screen shows the steps the agent really takes, as it takes them, with Fritts's matching poses. A real run takes about two minutes.
5. The finished plan opens in the same report screen the saved plans use (download PDF, explain a section). Share links work only for the saved plans for now, so for their own plan Fritts points to the PDF.
6. If something goes wrong (the daily limit is reached, the planner cannot be reached, the agent needs more information, or it times out) Fritts says so in plain words and offers "Back to my answers" or a sample plan.

## How it works

- `POST /api/sessions` saves the profile built from the form (`frontend/app/plan-mockup/live-run.ts`, `buildProfile`).
- `POST /api/sessions/{id}/runs` starts the agent on a background thread and answers at once. A real run is too long for one web request, which browsers and the hosting proxy can cut off.
- `GET /api/sessions/{id}/latest-run` is asked every 2.5 seconds. It returns the run with the steps taken so far, and the page shows them. When the status is `done` or `partial` the page builds the report from `output.plan_summary`.
- The classic planner is unchanged: it still uses `POST /api/sessions/{id}/messages`, which waits for the whole run.

## Cost and limits

A real run uses Claude credits (about $0.30 each in the five recorded demo runs).

- One run at a time per session.
- A daily cap on real runs across the whole site: `LIVE_RUNS_PER_DAY`, default **25**. When it is reached the page says the planner has done as many analyses as it can for today. Runs on the scripted model (tests, replays) are never counted.
- Set `LIVE_RUNS_PER_DAY` in the backend's environment (for example on Render) to change it.

## Testing without spending credits

- Backend: `backend/tests/test_live_runs.py` uses the scripted model and mock tools.
- Frontend helpers: `npm run check:live-run` (in `frontend/`) checks the form-to-profile code, the step list and every way a run can end, with the backend calls stubbed.
- To try the whole flow in a browser for free, run the backend with `LLM_PROVIDER=scripted TOOL_MODE=mock` and give the new session a saved transcript with `fixture_case`.

## Needed on the live site

The Vercel frontend calls the backend at `NEXT_PUBLIC_API_BASE_URL`. That backend must be running this code (the `runs` and `latest-run` routes) and have its own keys set (Anthropic, plus the city-data and price keys listed in `.env.example`). Until the backend is redeployed with this code, a real run from the live site shows the "couldn't reach the planner" message and the visitor can open a sample plan instead.
