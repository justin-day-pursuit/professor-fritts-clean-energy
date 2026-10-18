# Fritts experience: guided, conversational, animated front end

A spec for the character-led experience Mara described. It is kept separate from the working `/planner` page until she says to switch. Items marked **(proposed)** were added to the idea and can be struck.

## The idea, in her words

The visit should feel like a real personal experience, like walking up to a counter, a bank teller or someone's office and talking to a professional who helps you. Professor Fritts is a character who stays with you the whole way: he introduces himself, asks, confirms, works on your case in front of you, presents the report, and stays beside it to answer questions. It should be conversational and feel like a person is helping, not automated. Animations do not have to be crazy; they just have to make it feel real.

## The flow

### 1. Welcome (animated intro)
- Fritts appears and introduces himself, what he is about, and how he can help.
- One clear button to begin ("Let's begin").

### 2. Conversational intake (same fields as the form underneath)
- The form is broken into sections: Building; Money and goal; Backup power; What you already have; More detail (optional).
- Fritts speaks for each section: "Oh yes, I see your building..." / "Thank you for your information."
- If something was not given (for example the goal), he asks for it.
- After each section he repeats back what he heard and the user confirms with one of three choices: **Yes, that's right / No, I want to edit / I don't know**. "I don't know" leaves the field blank, and the plan then states what it assumed.
- He can read the building back from city records (tax lot, footprint, energy report) before asking the user to fill in the rest.

### 3. Fritts at work (the run)
- A timeline of each real step the agent is doing, with a matching animated scene of Fritts doing that step: researching in a book (city records), opening a solar-panel roof blueprint (roof and solar), placing solar on a roof, working the numbers (costs), and writing the plan (he is actually writing).
- Every scene and line of narration is tied to a real tool event, never a fake progress bar.

| Real step (tool) | Scene |
| --- | --- |
| `lookup_ny_building_records` | Reading the records |
| `get_solar_production`, `calculate` | Studying the roof and solar |
| `get_utility_rates`, `get_utility_tariff` | Checking prices |
| `search_ny_incentives_and_rules` | Reading the rules |
| `get_hazard_context` | Checking the flood map |
| `optimize_solar_storage` | Sizing the battery |
| `run_financial_model` | Running the numbers |
| final `write_roadmap` | Writing the plan |

- Narration is plain language, for example "I'm checking the city's energy report for your building."

### 4. Fritts presents the result
- He says the outcome in his own words, based on the real result: "I have your report: yes, you can reach your goal" or "actually, we need more information first". Other outcomes: needs a roofer first, reachable but over budget, not reachable.
- The report opens like a report opening in an AI chat. Open question: full page, or a panel beside him. **(proposed)** Full-width report with Fritts docked to the side; on a phone he becomes a corner bubble.
- The report content is what the plan page already shows (headline, confirm-first list, three plans side by side, roadmap, professionals, incentives, who to contact, the full report by the 13 sections with the data behind each). No information is removed.

### 5. Fritts beside the report (always available)
- **Download PDF** and **Share**.
- **"Would you like me to explain any section?"** The user picks a section from a list or types a question. Answers come only from the finished report, so no new numbers appear.
- **Run it again**: return to the intake with the answers filled in, edit, and re-run.
- Overall this is a chat on the site, but with Fritts present throughout.

## Principles
- Warm and professional; he never promises savings; every number keeps its label and its source link.
- Honest about what is scripted: his intake lines are scripted from the user's answers, and the plan itself comes from the real agent.
- Animations are simple illustrated moments, not heavy video. Respect reduced-motion, and show every spoken line as readable text too.
- Works on desktop and on a phone.

## What already exists to build on
- Logo and portrait: `frontend/public/fritts-logo.png` (one illustrated portrait, not a posed character).
- Storyboard of all the screens (static, no animation): https://claude.ai/artifact/2rjejyJv542uCi198f6C5p, copy in `reference/artifacts/fritts-experience-storyboard/`.
- Plan page design with real data: `frontend/app/plan-mockup/` (home, intake, running, results), with `data/plans.json` from five recorded real runs. These replay for free, with no Claude cost.
- Run events: every replay or run returns ordered `tool_call` and `tool_result` events that the timeline can play step by step. `frontend/lib/replay-playback.ts` already paces them.
- The plan summary (`output.plan_summary`) holds everything the report screen needs.

## Backend pieces needed (proposed)
1. **Live progress:** start a run in the background and poll its events. Today a run is one blocking request.
2. **Explain a section:** a small separate endpoint that sees only the finished report and uses the same labeling rules. It costs about 2 to 6 cents per question; put a cap on it for demos.
3. **PDF export:** a print stylesheet or a server-generated file.
4. **Share link:** needs saved plans and a privacy decision, so do it last.

## Build phases (proposed)
1. **Core:** intro, conversational sectioned intake with the confirm buttons, the timeline with simple scene icons driven by replay events, report reveal with Fritts docked, re-run, and PDF. Build and test entirely on the five recorded runs (free).
2. **Fritts Q&A:** explain a section and ask a question.
3. **Art upgrade:** richer Fritts animations (reading a book, unrolling a blueprint, placing panels, writing), plus a phone and accessibility pass.
4. **Later:** the share link.

## Decisions still open
- **Character art:** a simple vector Fritts to start, or artwork Mara supplies or generates. Suggested set: greeting, listening, reading, working a blueprint, presenting, thinking.
- **Intake voice:** scripted lines (recommended; free and predictable) or AI reading free text.
- **Report opening:** full page with Fritts in a corner, or a panel beside him.
- **Share link and login:** out of scope until the privacy decision.

## Acceptance (proposed)
- A user can go from welcome to a finished plan using only the recorded runs, with Fritts speaking at every step, and never sees a spinner without a matching real step.
- Every confirm choice (Yes / Edit / I don't know) changes the data correctly.
- The report screen shows everything the current plan page shows.
- No live Claude call or spend is needed to build or test phase 1.
