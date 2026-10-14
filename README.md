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

## Team

Justin Day, Mara Munoz
