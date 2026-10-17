# What Professor Fritts provides: inputs, address lookups, outputs, and whether it is worth it

Written Oct 16, 2026, from the code on the `demo-prep` branch (v6 plus the replay menu, roof suggestion, existing-systems section and budget-gap changes) and from the live runs we did on Oct 15. Everything below was checked against the code or a run; where something is a judgment or a guess, it says so.

## The question (recorded)

> What does our AI agent currently provide for a user? Give me all the inputs, in a list, that the user provides. Ideally, is everything calculable and searchable for that address? What output does the agent give? Be very thorough and tell me everything the agent gives the user when it is given what it needs, and how this is worthwhile or useful at all.

## The short answer

- **The user gives it a lot.** About 25 form fields, one chat question, and optionally uploaded files. Only three fields are strictly required by the form (address, borough, roof area) and four by the agent (borough, budget, goal, and the state, which is fixed to NY).
- **From just an address, the agent can find on its own:** the tax lot, floor area, floors, year built, owner class, landmark or historic-district status, the building outline (a roof-area suggestion), solar output for that exact roof location, and the New York average commercial electricity price. That is real, live data.
- **It cannot find from an address:** the building's actual electricity use, its real tariff, current incentive status, its flood and heat risk (it returns a saved sample, not that address), battery sizing, roof type and condition, or what the building already has installed.
- **It outputs a 13-section plan** with three costed scenarios (efficiency only, efficiency plus solar, and a full path with backup power), a six-phase roadmap, the professional reviews required before any money is spent, and a confidence summary. Every number carries one of four labels, a confidence level and a source or calculation ID. A run takes about two minutes.
- **Is it worthwhile?** As a screening and "what do we need to check and who do we call" tool for a NYC public building, yes, and that is a real job. As a source of decision-grade numbers, not yet: the cost prices and efficiency savings are our own planning benchmarks with no cited source, and the tariff, incentives, hazard and battery data are saved samples. Nobody outside the team has tested it. The honest verdict is in section 6.

## 1. What the user provides (the inputs)

### The intake form (25 fields)

Required by the form to enable sending: **address, borough, roof area.** Required by the agent's first safety check: **a NYC borough, a capital budget, and an energy goal** (otherwise it asks once, then stops). Everything else is optional, and a blank field is flagged in the plan ("we don't know X") instead of being invented.

| Group | Field | How the agent uses it |
| --- | --- | --- |
| **Who** | Contact name, building name | Display only. Not used in any calculation. |
| **Where** | Address | Geocoded to a tax lot; drives every city-data lookup and the solar location. |
| | Borough (pick-list of the five) | Required. Anything outside the five boroughs stops the run as out of scope. |
| | State | Fixed to NY. |
| **Building** | Building type | Free text. Used to spot parks (a "park" building triggers a parkland review). Also reaches the plan's wording. |
| | Floor area (sq ft) | Efficiency cost (price per sq ft), the baseline benchmark if no kWh was given, and a cross-check against city records. |
| | Year built | Cross-checked against city records; plan context. |
| **Roof** | Roof type (flat, pitched or sloped, flat and pitched, dome/tower/other) | Anything but flat means solar is **not sized** until a usable area is verified by an engineer or roofer. |
| | Roof area (sq ft) | Sizes the solar array (usable roof = 55% of it, then 66 sq ft per kW). Cross-checked against the city's building outlines. The form has a "suggest from city records" button. |
| | Usable roof area verified by an engineer or roofer (only shown for non-flat roofs) | Unlocks solar sizing on a pitched or mixed roof. |
| | Roof replaced (year) | Flagged if blank. Plan context (re-roofing before solar). |
| **Energy** | Utility | Free text. The plan assumes Con Edison for every building and says so. |
| | Annual kWh | The baseline for the 30% goal. If blank, the agent uses a benchmark of 9 kWh per sq ft (labeled an assumption, low confidence). |
| **Money** | Budget amount, budget year, capital or annual | The amount caps Scenario B's solar and sets "within budget / over budget" for every scenario. **Capital vs annual and budget year are not modeled differently**; they appear in the plan's wording only. |
| **Goal** | Energy goal (free text), target year | The agent turns a percentage goal ("cut 30%") into a fraction. Other goals (net-zero, "go solar") are discussed in words but **not quantified**. Target year is wording only; no time-value-of-money is modeled. |
| **Resilience** | Critical loads (free text) | Named in the plan. **Not converted to kilowatts.** The backup-power numbers come from a fixed sample (see 2). |
| | Critical load hours | **Collected by the form but never used by the backend.** |
| **What you already have** | Existing solar (kW), what it makes (kWh/yr), other renewables, efficiency work already done | A new array is sized only on the roof left after the existing one; the plan must say how these were taken into account. Leaving the whole section blank triggers "you didn't tell us" and the plan asks once. |

### The chat question
One question, such as "How can we cut grid power 30% by 2030 on $400k and keep the building open as a cooling center?" The agent also reacts to requests inside it: it refuses to "skip the engineer" or "confirm the roof can hold the panels," refuses to guarantee savings, and says a rule from outside NYC (for example a California rebate) does not apply.

### Uploaded files
- A CSV named like "bills" or "kwh" with `month` and `kwh` columns is **parsed and stored** (monthly values and a total).
- **Nothing reads it.** The agent only sees the typed form, so an uploaded bill does **not** set the annual kWh. The form label ("Annual kWh, or upload bills below") promises more than the code delivers. This is the most misleading gap in the intake today.
- Any other file (PDF, photo, spreadsheet) is saved as "received, not parsed."

## 2. What can be found from the address, and what cannot

"Live" means fetched from the real source on every run. Everything in the first table works for any NYC address today.

### A. Found automatically, live
| What | Source | Caveats |
| --- | --- | --- |
| The tax lot (BBL) and coordinates | NYC GeoSearch | Often a "fallback" match at 0.8 confidence; the lot's official street can differ from the one typed (it is flagged). |
| Floor area, lot area, floors, year built, building class | NYC PLUTO | Public records are often wrong or stale; the agent shows both numbers when they disagree (P.S. 38: 17,620 vs 55,860 sq ft). |
| Landmark or historic-district flag | PLUTO | One flag covers both an individual landmark and a historic district; it does not say which. |
| Building outlines on the lot, and a suggested roof area | NYC building footprints | A footprint is ground area, not a measured roof. It cannot see pitch, towers, equipment, or buildings that are not yours. |
| Solar output at that roof for the array size | NREL PVWatts v8 (flat-roof defaults: 10 degree tilt, facing south, 14% losses, shown as a range for 10 to 18%) | Not tuned to the real roof orientation or shading. |
| Electricity price | US Energy Information Administration, New York commercial average, last 12 months | A state average, **not this building's tariff**. |

### B. Exists in public data, verified reachable, but not connected to the agent
| What | Why it matters | Source |
| --- | --- | --- |
| **Actual annual grid electricity (kWh)**, peak demand (kW), gas and oil use, ENERGY STAR score, and **solar already generating on site** | This is the single biggest gap. It would remove most typing: address in, baseline out. We used it by hand to build every real test case. | NYC LL84 benchmarking (large buildings, roughly 25,000 sq ft and up) |
| **FEMA flood zone** | The hazard tool currently returns a saved sample (a Queens site) for every address. The real FEMA lookup works and is free; we used it by hand. | FEMA flood map service |
| Whether the lot is city parkland | Today only a keyword in "building type" triggers a parkland review. The owner field (for example NYC Parks) is in PLUTO but not read. | PLUTO owner |

### C. Not findable from an address (needs the user or a professional)
Roof type and condition; when the roof was last replaced; structural capacity; shading and rooftop equipment; the building's real tariff and demand charges (needs bills); the hourly load shape; critical loads in kW; what the budget really is; existing systems the city does not list; interconnection capacity; and the current **status of incentive programs** (needs reading official pages; we did this by hand once for the demo building).

### D. Still saved samples in a live run (not about the address)
| Tool | What it returns today | Plan treatment |
| --- | --- | --- |
| Tariff | A fictional Con Edison SC-9 Rate I from case 1 | Flagged for the user to confirm |
| Incentives and rules | A fictional list from Oct 2025 | Flagged as sample; **no incentive is counted in net cost** |
| Hazard | A fictional Queens flood and heat rating | Flagged as sample |
| Battery sizing | A fixed 960 kWh / 120 kW | Labeled an assumption; the backup-hours figure is therefore a placeholder, not sized to the building |

The one exception is the P.S. 236 demo case (real incentive snapshot and real flood zone). See `documentation/demo-case.md`.

## 3. What the agent calculates, and on what basis

| Calculation | How | Basis |
| --- | --- | --- |
| C1 usable roof | Roof area times 0.55 | Our assumption (setbacks, equipment, access paths) |
| C2 array size | Usable roof divided by 66 sq ft per kW | Our assumption for a flat commercial layout |
| Solar output | PVWatts for that array at that location, low to high | **Real model**, flat-roof defaults |
| C3 solar offset | Solar kWh divided by annual use | Arithmetic |
| C4 bill savings | Solar kWh times the New York average price, low and high | Arithmetic on a state average, not the building's tariff |
| Scenario A | LED and controls: 10-20% savings at $4-8 per sq ft | **Our benchmark, no cited source** |
| Scenario B | A plus solar sized to the leftover budget, capped at the whole roof; solar $3,000-4,500 per kW | **Our benchmark, no cited source** |
| Scenario C | Deep efficiency (15-25% at $10-16 per sq ft) plus the whole-roof array plus a battery ($600-1,000 per kWh) | **Our benchmark, no cited source** |
| Federal credit | 30% of solar and battery cost, only if the incentives tool says the program is open and not stale or sample | Statute-based, but only counted for the demo building |
| Cut in grid use | Efficiency plus solar that replaces power still used; **never above 100%**; surplus is reported separately and not counted | Our rule |
| Simple payback | Net cost divided by yearly savings, as a range | Simple, not the full SAM model |
| Budget strain and gap | Upfront cost against the budget; the dollar gap when over | Our rule |
| Backup hours | Usable battery energy (85-100%) divided by the critical load | Sample battery and sample load |

**Not modeled at all:** demand charges and time-of-use rates, a real tariff, price escalation, panel degradation, operating costs, financing, net metering and export credits, roof repair or strengthening costs, interconnection upgrade costs, permits, shading, tilt and orientation tuning, heat pumps and electrification, gas and oil, building simulation, and carbon or Local Law 97 compliance.

## 4. What the agent outputs

### The plan: 13 sections
1. **Summary and goal status:** can the goal be reached, with which scenario.
2. **Building profile and data provenance:** what you entered, what the city says, and where they disagree.
3. **Assumptions register:** every assumption, numbered (A1, A2, and so on).
4. **Baseline and efficiency opportunities:** your baseline and the efficiency measures.
5. **Solar assessment with calculations:** usable roof, array size, yearly output (range), offset, savings.
6. **Scenario comparison:** A, B and C on share of the goal, upfront cost, net cost, payback, budget strain, backup hours, and the budget gap when a scenario costs more than the budget.
7. **Cost, financing and incentives:** programs with status and retrieval date; closed or uncertain programs listed and left out of net cost.
8. **Priority roadmap:** phases 0 to 5 (confirm data and budget, professional reviews, efficiency, permits and interconnection, solar, battery and verification).
9. **Resilience and reliability:** backup hours, which loads, flood siting.
10. **Required professional reviews and permits:** always a structural PE or RA analysis, a roof condition survey, a licensed electrician, FDNY rooftop access and Con Edison interconnection; plus, when triggered, a Landmarks Preservation Commission review (advisory on parkland), a parkland review by counsel, a flood-zone review, and the NYC sustainable-roof rule.
11. **Path to net-zero and learning resources.**
12. **Gaps, conflicts and confidence summary:** what is missing, what disagrees, and what would raise confidence.
13. **Sources.**

### What every statement carries
One of four labels: **FACT, ESTIMATE, ASSUMPTION, RECOMMENDATION**; a confidence (high, medium or low); a source link or a calculation ID; and, for numbers, a low and a high with units. Check 4 refuses to release a plan with an unlabeled number. A typical plan has 47 to 74 labeled statements.

### What else comes back
- A **run log** of every check, tool call and tool answer; the data flags (sample, stale, mismatch, missing); downloads as Markdown or JSON; and, on live runs, the token use and estimated cost.
- Designed states instead of errors: a **partial** plan when something could not be done (a pitched roof, a failed tool), a single **question** when the budget or goal is missing, and a plain **out of scope** message for a building outside NYC.
- Behaviors that protect the user: it will not size solar on a roof that is not flat, will not certify a roof, will not promise savings, ignores instructions hidden in retrieved pages, and states plainly when a scenario costs more than the budget.
- **Chat follow-ups are not cheap.** The agent has no memory between messages: every message re-runs the whole agent (about two minutes and real cost) on the current form. To explore "what if the budget were $1M," change the form and re-plan.

## 5. What we have seen it produce
| Building | Outcome |
| --- | --- |
| P.S. 236, Bronx (demo case, real data, scripted plan text) | Goal reached by Plan B within an $800,000 budget; backup power $470k to $1.24M over budget; real incentives snapshot |
| P.S. 38, Staten Island | Goal near but not certain on $600,000; city and intake floor areas disagree by 3x |
| Red Hook Recreation Center | Goal reached within budget; backup power far over; landmark, parkland and Sandy flood history all handled |
| Jefferson Market Library | Solar not sized (pitched roof); plan tells the user to get a roofer first |
| P.S. 24, Bronx | Existing solar already fills the roof; efficiency only |

Each of the four live runs finished as designed, and the plans caught real data problems. See `documentation/real-cases.md`.

## 6. Is it worthwhile or useful?

### What real value it delivers today
1. **A fast, structured first look.** In about two minutes it joins city records, a real solar model, electricity prices, scenario costing and a referral checklist. Doing that by hand means several tools and a spreadsheet.
2. **It says how sure it is.** Every number is labeled, ranged and sourced, and it is built to refuse, flag and ask before guessing. Most AI answers sound equally confident about everything; this one doesn't. That is the strongest idea in the product.
3. **It tells you what to do and who to call before spending money.** The checklist (engineer, roofer, electrician, FDNY, Con Edison, and the conditional landmark, parkland and flood reviews) is useful by itself, and it is mandatory in every plan.
4. **It is NYC-specific** in ways a generic tool is not: the five-borough scope, Con Edison, DOB and LPC reviews, the Solar Schools pipeline, and the sustainable-roof law.
5. **It exposes data problems.** It flagged that P.S. 38's records disagree three-fold and that P.S. 24's roof was already full.

### What it does not deliver yet, in plain terms
- **The cost and savings numbers are not sourced.** The solar, battery and efficiency prices and the 10-20% savings are our own planning benchmarks. No published cost study backs them, and no plan has been compared to a real installer quote. The PRD's own target is that a later quote falls inside our range at least 80% of the time. We have no evidence either way.
- **Four of the inputs that matter most are samples** in a live run (tariff, incentives, hazard, battery), and the user must type the baseline electricity use.
- **Savings ignore the building's real bill structure.** Demand charges, time-of-use rates and net metering can change savings a lot, and none are modeled.
- **The backup-power answer is a placeholder.** It does not use the user's critical loads.
- **Nobody outside the team has tested it.** No pilot user, no time-saved measurement, no usefulness rating.

### The PRD's own success targets, as of today
| Target | Status |
| --- | --- |
| 100% of numbers labeled, with confidence and an ID | Enforced by code; met by design |
| Required professional referrals never missed | Enforced by code for the five standard reviews |
| No stale or non-NYC rules used | Enforced for scope; stale data is flagged, not silently used |
| Calculations reproducible within 1% | The arithmetic is deterministic and PVWatts inputs are logged; not formally re-run in this session |
| 95% of factual claims fully supported | **Not measured**: no hand review |
| Cost ranges contain real installer quotes 80% of the time | **Not measured**, and the prices are unsourced |
| 40% less planning time | **Not measured**: no pilot users |
| Usefulness 4 out of 5, and used in a real board discussion | **Not measured** |

### The honest verdict
- **Useful today as:** a screening and preparation tool. It helps a facilities manager decide whether solar and efficiency are worth pursuing, what to verify, who to call, and what to ask for, with the uncertainty visible. For a class demo it also shows a real design idea: an AI planner that is honest about what it does not know.
- **Not yet useful as:** a source of numbers to put in front of a board or to commit money against. An expert could produce a rough first screen in about an hour with PVWatts and a spreadsheet; the agent's edge is speed, NYC context, and consistent honesty, not accuracy beyond that.
- **The main risk:** plausible-looking dollar ranges from unsourced benchmarks. The labels and the "planning estimates, not quotes" wording reduce that risk, and they don't remove it.

### What would make it clearly worth using (in the order I would do it)
1. **Auto-fill the baseline from LL84** (address in, real kWh, peak demand, gas and oil, and existing solar out). Removes most typing and replaces the most important user-entered number with a real one. Small to medium effort, and the best "wow" for a demo.
2. **Read uploaded bills** (the code already parses a simple CSV; nothing uses it). Small effort, and it fixes the most misleading form label.
3. **Cite the prices.** Replace the benchmark prices and savings percentages with published, cited cost data, and show the source in the plan. Medium effort, mostly research, and it is the biggest credibility fix.
4. **Make hazard live** (FEMA works and is free). Small effort.
5. **Real tariff and demand charges** (OpenEI key exists; the hard part is choosing the right rate). Medium to large.
6. **A real incentives reader** for a short list of official pages, with the 7-day freshness rule. Large; the build plan's biggest risk.
7. **Battery sizing from the user's actual critical loads.** Medium, and it needs a load profile for a real optimization.
8. **Test it with two or three real facilities managers** and, if possible, compare one plan with a real installer quote. Small effort, large learning.

## 7. What we do not know
- How close the cost ranges are to real quotes.
- Whether facilities managers would trust, use or pay for it.
- How the PLUTO and LL84 data errors affect plans on buildings we have not tried (we have run seven).
- Whether prompt caching works against the real API (built and tested with a fake client only).
- Whether Far Rockaway (PSEG Long Island, not Con Edison) should be in scope (still an open question).

## Where this came from
Code: `backend/tools/`, `backend/agent/`, `backend/api/`, `frontend/components/intake-form.tsx`. PRD: `documentation/Building_Renewable_Energy_Planner_PRD_v3.md`. Runs and data: `documentation/real-cases.md`, `documentation/demo-case.md`, and the five saved runs under `backend/mocks/fixtures/`.
