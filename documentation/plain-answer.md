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

## The five sample plans

Their building details are now filled from the city's records, the way the website fills them for a visitor (`python manage.py build_city_intakes`), so the "please confirm" list holds only real items. Re-record them with live runs, and re-export the saved plans with `python manage.py export_plan_summaries --out ../frontend/app/plan-mockup/data`.
