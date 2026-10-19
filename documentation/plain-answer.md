# The plain-words answer at the top of every plan

Every real plan now opens with one short paragraph that answers the question in plain words. It sits on the report screen between the headline ("The short answer · …") and the "Please confirm first" list, at the top of the written plan ("In plain words"), and at the top of the PDF. The sections below it are the evidence.

## Why

The agent used to hand back about 45 separate labelled statements across 13 sections. They are good for checking where each number came from, but nothing connected them into an answer. A reader had to do that themselves.

## Who writes it, and how it is checked

The agent writes it as part of the plan it already writes (the `plain_answer` field of `write_roadmap`), so it sees the whole picture and it is saved in the recording, which means saved plans replay for free. The instructions are in `backend/agent/prompts/system_prompt_v5.md` ("The plain-words answer"). They are general, not tied to a building: what was asked and the answer, what the building already has, what limits it, and what to do next. Record mismatches are left out of it and shown under "Confirm first" instead.

Code checks it before a live plan is accepted (`agent/checks.py`, `_plain_answer_issues`). A plan that fails is sent back once, as with every other check:

- it must be there (live runs only, so plans recorded earlier still replay);
- about 50 to 240 words;
- no promise of savings, no internal names or ids;
- every number in it must already appear in the plan's own statements, so it cannot say more than the plan supports;
- it must say why solar was not sized when a roof rule turned it down, and it must not talk about entered values that differ from the city's records (those are listed under "Confirm first").

## Two data fixes that came with it

- **Solar readiness is yes, no, or blank.** A blank from the city used to count as "no", so buildings the city never rated were reported as "not solar ready". Only an explicit "no" is a warning now.
- **A roof rule saying no is not a failed lookup.** "The existing array already fills the roof" and "the roof is not flat" are decisions. The report says the reason instead of "could not return data".

## The six sample plans

Their building details are now filled from the city's records, the way the website fills them for a visitor (`python manage.py build_city_intakes`), so the "please confirm" list holds only real items. Re-record them with live runs, and re-export the saved plans with `python manage.py export_plan_summaries --out ../frontend/app/plan-mockup/data`.

The sixth sample, the Flushing Library in Queens (41-17 Main Street, a real Queens Public Library building), was not recorded from a Claude run. Its plan text was written by hand by following the agent's own instructions step by step, using the real results of the city, solar, price, flood and incentive lookups (all free), so it cost no credits. It is listed like the other samples. Its sources and numbers are real; only the wording was authored.

## The answer pill and headline

The pill on each home card and the headline at the top of the report come from one rule, `decide_outcome` in `backend/agent/plan_summary.py`, so the card, the report and the PDF always say the same thing. It looks at whether a plan reaches the goal (tested at the low end of its range) and whether it fits the budget:

| Answer | Pill | Colour |
|---|---|---|
| Reaches the goal within budget | Goal reached within budget | green |
| The same, but the city rates the roof not solar ready, poor or 20+ years old (the costs leave out replacing it) | Goal reached, roof review first | blue |
| The same, but the visitor asked for backup power and the plan has none | Goal reached, no backup yet | amber |
| Reaches the goal, but may cost more than the budget | Reachable, may run over budget | amber |
| Reaches the goal, but costs more than the budget even at the low end | Reachable, over budget | red |
| No plan is sure; the best reaches the goal only at its high end and fits the budget | Goal possible, not guaranteed | amber |
| The same, but the best does not fit the budget | Not within budget | red |
| No plan reaches the goal | Goal not reached | red |
| A pitched roof, no verified area | Needs a roofer first | blue |

When a plan has both a roof problem and no backup, the roof comes first, because it can change the whole plan. Whether the visitor asked for backup is read from their question (words like outage, blackout or battery).

The three plan cards each show two pills: whether that plan reaches the goal (green reaches it, amber only at its best, red short of it) and whether it fits the budget (green fits, amber may run over, red over). "Recommended" sits on the card's top edge.
