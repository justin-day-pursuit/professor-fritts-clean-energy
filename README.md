# Professor Fritts

https://github.com/user-attachments/assets/aade091b-ec65-4933-92f2-294a5a35e965

Landing, intake for P.S. 236, live analysis, report, and a follow-up.

**Your guide to renewable energy for schools and public buildings.**

**Try it live:** [professor-fritts-clean-energy.vercel.app](https://professor-fritts-clean-energy.vercel.app)

## What it is

Professor Fritts is an AI assistant that helps New York City building managers (school districts, libraries, parks) figure out how to cut their energy use and go solar.

You tell it about a building and your goal. It looks up real city data, runs the numbers and hands back a clear, step-by-step plan, with costs, so you know what to do first and what it will take.

## The problem

Going solar is confusing. Managers of public buildings have to sort out roof space, costs, rebates and city rules, and most don't have an energy expert on staff. Fritts does that first round of research in minutes and tells you which experts to call next.

## What makes it different

- **You can trust the numbers.** Every figure is marked as a fact, an estimate, an assumption or a recommendation, and shows where it came from. Nothing is made up.
- **It compares options.** You get at least three scenarios side by side, so you can see the trade-offs instead of one take-it-or-leave-it answer.
- **It knows when to call a human.** The plan names the professional reviews (engineer, roofer, landmarks and flood experts) needed before any money is spent.
- **It is honest about what it doesn't know.** If a data source fails, the plan says so instead of guessing. It never promises savings.
- **It checks itself.** Built-in safety checks catch unlabeled numbers, missing referrals and out-of-area requests before a plan is shared. These are rules in code, not the AI grading its own work.
- **It stays on topic.** It only plans for NYC buildings and politely declines anything outside that, such as a New Jersey town hall.
- **It resists tricks.** Web pages with hidden instructions aimed at the AI are spotted and ignored.

## See it work

Open the app, click **Load Dana's example** (a sample Queens public library), and send her question. You can also replay saved plans for real NYC buildings, including a Bronx school (P.S. 236), a Red Hook community center and a landmark library in Manhattan.

We tested it on 9 sample buildings built to trip it up, such as no budget given, a building in a flood zone, a landmark, and a request to "guarantee my savings". We also ran it on 4 real NYC buildings.

## What's real and what's still a stand-in

Built and working with live data:
- NYC building records and roof size suggestions
- Solar power estimates
- NYC electricity prices
- Cost and payback calculations

Still using saved sample data (clearly labeled in every plan):
- Rebates and incentive status
- Battery sizing
- Flood and storm risk

Coming next: live incentive lookups and a full financial model.

## Built with

Next.js (website), Python with Django and FastAPI (backend), Supabase (database), Claude by Anthropic (the AI), deployed on Vercel and Render.

## Run it yourself

1. Copy `.env.example` to `.env` and add your Anthropic API key.
2. Install: `cd frontend && npm install`, then `cd backend && python3.12 -m venv .venv`, activate it and run `pip install -r requirements.txt`.
3. Start everything with `./scripts/dev.sh`, then open `http://localhost:3000`.

No API key? Set `LLM_PROVIDER=scripted` in `.env` to play back saved examples for free.

## Learn more

- [Product Requirements Document](documentation/Building_Renewable_Energy_Planner_PRD_v3.md)
- [How the agent works](documentation/user-flow/Professor%20Fritts%20Agent%20Flow.md)
- [Real building results](documentation/real-cases.md)
- [Demo case: P.S. 236](documentation/demo-case.md)

## Named after

Charles Fritts (1850-1903), the New York inventor who built one of the first solar cells in 1883 and put solar panels on a New York City rooftop in 1884.

## Team

Justin Day, Mara Munoz
