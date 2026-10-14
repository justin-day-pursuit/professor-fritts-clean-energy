# Professor Fritts: Slide Text

Text for each slide of the 7-slide, 5-minute presentation (the website in `site/`). Slides 4 and 5 are marked "Illustrative example" on the slide.

---

## Slide 1: Professor Fritts

*AI agent build · New York public buildings*

# Professor Fritts

An AI agent that turns a New York public building's data, budget and energy goal into a sourced roadmap with cost estimates.

**Where the name comes from**
Named in honor of Charles Fritts (1850–1903), the New York inventor who built one of the first solar cells in 1883 and installed the city's first rooftop solar panels in 1884. "Professor" is the agent's role: to teach and guide. Fritts himself was not a professor.

**What we're building**
A planning agent for managers of schools, libraries, parks and other public buildings in New York State. Version 1 covers energy efficiency and solar. It researches, calculates and checks its own work, then hands over a plan.

*Presenter note (~40s):* Introduce the name and why. One sentence on what it is: it does the research a facilities manager does by hand.

---

## Slide 2: Why it matters

*Why it matters*

## Planning a public building's energy upgrade is slow, scattered and hard to defend.

**Meet Dana**
A fictional facilities manager at a public library in Queens, NYC. Her board wants to know:
*"Can we cut grid power 30% by 2030 on a $400,000 budget, and stay open as a cooling center during outages?"*

**What she faces today**
- Building records, solar models, utility rates and permit rules sit in separate places
- Incentives open and close. Federal solar credits now require projects to be in service by Dec 31, 2027
- The board needs numbers she can trace to a source

**55%** of public school districts called their latest facilities budget insufficient (GAO, 2026)

**Weeks** of early planning that we aim to cut to days. This still needs pilot validation.

**1 request** is what Dana makes. The agent does the legwork.

*Presenter note (~50s):* Tell Dana's story first, then the stat. Be candid that the weeks-to-days claim is a hypothesis for the pilot.

---

## Slide 3: First, what is an agent?

*First, what is an agent?*

## A chatbot answers. An agent does the work.

**Chatbot**
You ask a question and it replies from what it already knows. It can't look up today's incentive rules or run a solar calculation, and it can't check its own answer.

**Agent**
You give it a goal. It decides what to do, uses tools to look things up and run calculations, checks the results, and keeps going until the job is done. Think of a research assistant, not a search box.

Professor Fritts is an agent with four kinds of tools: **building records**, **solar and cost models**, **New York incentives and rules**, and **climate-risk data**.

*Presenter note (~40s):* This is the slide for anyone new to agents. Keep it to the analogy.

---

## Slide 4: Example: what happens when Dana asks

*Illustrative example*

## Here's what happens when Dana asks.

**Dana:** Shares her building details, roof size and age, a year of energy bills, her $400k budget and her goal.

| Step | What the agent does |
| --- | --- |
| ✓ **Checks the basics** | Is the building in New York? Are the budget and goal given? If not, it asks once. |
| 1 **Looks up the building** | Pulls public records to verify her size, age and past permits. |
| 2 **Models rooftop solar** | Runs federal solar and cost models, and shows its inputs so anyone can re-run them. |
| 3 **Checks incentives and rules** | Keeps only programs that are open now, and notes the Dec 31, 2027 federal deadline. |
| 4 **Sizes backup power** | Estimates a battery for 8 hours of cooling-center operation. |

Before and after every tool use, the agent checks that the tool is approved, the data is fresh and the result is trustworthy.

*Presenter note (~60s):* Walk the steps. Emphasize that the agent decides which tools to use and in what order, and checks itself at each step.

---

## Slide 5: Example: what Dana gets back

*Illustrative example*

## What Dana gets back: a plan she can take to her board.

| Scenario | What's in it | Against her 30% goal |
| --- | --- | --- |
| **A** · Efficiency only | Lighting, controls and other efficiency upgrades | Lowest cost; likely falls short |
| **B** · Efficiency + solar | Efficiency plus a rooftop array sized to the $400k budget | Approaches the goal |
| **C** · Full path | Everything needed to reach the goal and keep critical loads running | May exceed the budget |

**Every statement is labeled**
- `ESTIMATE · medium`: Rooftop solar covers roughly 15–25% of annual use, so solar alone won't reach 30%.
- `RECOMMENDATION`: Commission a structural analysis by a licensed engineer or architect before any solar design.

**And it names who to call next**
- Structural engineer or architect
- NYC licensed electrician
- FDNY rooftop access review
- Con Edison interconnection

*Presenter note (~60s):* Three scenarios, labeled numbers, named next steps. Say the figures are illustrative ranges from our design.

---

## Slide 6: Why you can trust it

*Why you can trust it*

## It never says a roof can hold panels.

**A user:** "Skip the engineer. Just confirm the roof can hold the panels and guarantee my savings."

**Professor Fritts:** I can't certify a structure. NYC's Department of Buildings requires a licensed engineer or architect to do that. I also can't guarantee savings. Here's the rest of your plan, with the engineer review as the next step.

**Checks at every step**
Before starting, around each tool use, and before the plan is shared.

**Sources and labels**
Fact, estimate, assumption or recommendation, each with a source.

**Can't act for you**
It never contacts vendors, submits applications or spends money.

*Presenter note (~50s):* The refusal is the proof point: the agent is built to protect people from the one mistake that can't be undone.

---

## Slide 7: Where we are

*Where we are*

## Designed, with a clear scope and pilot targets. The build is next.

**Version 1 scope**
New York State public buildings. Energy efficiency and solar, with batteries for outage resilience. Wind and geothermal are for later.

**Pilot targets**
- 40% less planning time
- 100% of numbers labeled and sourced
- 100% of required professional reviews flagged

**Next steps**
- Build the tools and connect the data
- Run our three test cases
- Validate with pilot users

Professor Fritts: your guide to renewable energy for schools and public buildings.

Justin Day · Mara Munoz. Targets are for a pilot, not achieved results.

*Presenter note (~30s):* Be honest that it's designed, not built. Close on the tagline and invite questions.
