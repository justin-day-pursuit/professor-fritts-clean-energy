# NYC-Version: changes to the build plan

**Decision (Oct 15, 2026):** Professor Fritts is now **NYC only** (the five boroughs: Manhattan, Brooklyn, Queens, the Bronx, Staten Island). It was "New York State and NYC".

This file sits next to the original [Build Plan](<Building Renewable Energy Planner — Build Plan.md>) and the [PRD](Building_Renewable_Energy_Planner_PRD_v3.md). **Those two files are not edited.** Where this file and they disagree, **this file wins** until the originals are updated.

For coding agents: treat any "New York" or "New York State" scope wording in the plan, PRD, prompts, README or code as "NYC (five boroughs)", and apply the rules below.

## What does NOT change

- **State programs still count.** NYSERDA, NY-Sun, state tax credits and federal incentives still apply to a NYC building, so they stay in the incentives search and the approved sources list. NYC only limits *where the building is*, not which programs we look up.
- Blocks v0 to v2 stay as built. Labels, ranges and the 13 sections do not change.
- The tools stay the same. NYC Open Data / PLUTO already only covers NYC.

## Changes to the Build Plan, section by section

| Where in the plan | Old wording | New rule |
| --- | --- | --- |
| Decisions to lock | (none) | Add: "Scope is NYC, the five boroughs. State and federal programs are still in." |
| Accounts and keys | NYC Open Data token, "check whether it also covers data.ny.gov" | data.ny.gov is no longer needed. The NYC Open Data token is enough. |
| v3 goal, validator | "NY-only rules" | "NYC-only rules": the validator rejects rules from outside NYC (for example a California rule, or an upstate-only rule). |
| v3 goalpost | "A New Jersey building is stopped as out of scope" | Stop **any non-NYC building**: New Jersey, and also upstate NY, Long Island outside the city, Westchester. Test at least NJ and Buffalo. |
| v3 `approved_sources.yaml` | "official NY, NYC, federal and utility pages" | Keep state pages. Drop utility pages for any utility other than Con Edison (see "Open question" for PSEG Long Island). |
| v4 goal / goalpost / branch `evals/case2` | Case 2 = **Erie County elementary school** | Case 2 is replaced (see below). Erie County is upstate and out of scope. |
| v6 extra cases | "outside New York" | "Outside NYC": one upstate NY building, one New Jersey building. |
| Risks table | "Upstate buildings have thin public records" | Remove the row. City records cover every NYC lot. |
| Risks table | "Picking the right utility tariff" | Simpler: it is Con Edison in almost every case. Still show tariff name and effective date, and flag it for the user to confirm. |

## Replacement for eval case 2

Case 2 existed to test the hard cases, not Erie County itself. A NYC school tests the same things.

- **Building:** a fictional elementary school in the Bronx or Staten Island.
- **Intake:** no bills uploaded. Roof age unknown (public records suggest about 22 years). Budget of USD 250,000 with no year or type.
- **Cache:** the saved record for a state or city school program is 120 days old and says "open". The live official page says "closed".
- **Expected result (same as before):**
  - Asks once for bills and the budget year and type, then continues.
  - Baseline uses benchmark EUI (ASSUMPTION, low confidence).
  - Recommends a roof survey and likely re-roofing before solar, early in the roadmap.
  - Detects the stale record, refreshes it, saves the new "closed" version, and leaves the program out of net cost.
  - Shows the cached vs. live conflict.
  - Confidence summary reports low overall confidence and lists the data that would raise it.

The v4 goalpost text stays the same. Only the building changes.

## Changes to the PRD (when someone updates it)

- Section 3 **Scope**: "New York State, including NYC" becomes "NYC (five boroughs)". Keep "state and federal programs apply".
- Task step "If the building is outside New York, say it is out of scope and stop" becomes "outside NYC".
- Golden example 2 (Erie County) is replaced by the case above.
- Mandatory referrals: drop wording that implies upstate utilities. Keep structural PE/RA, roof survey, NYC-licensed electrician, FDNY rooftop access, Con Edison interconnection.

## Changes needed in the code and repo (not done yet)

| File | Change |
| --- | --- |
| `backend/agent/checks.py` (`run_check1`) | It currently accepts any New York State building. Require a NYC borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island, or the city name). Anything else stops with `out_of_scope`. |
| `backend/agent/prompts/system_prompt_v2.md` | "New York public buildings only" becomes "NYC (five boroughs) public buildings only". |
| `README.md` line 13 | "New York State and NYC only" becomes "NYC only". |
| Intake form and `frontend/lib/*` | Borough becomes a required pick-list of the five boroughs. The state field can be fixed to NY. |
| `backend/tools/geocode.py`, `live_records.py` | The county fallback exists for non-NYC addresses. Re-check whether it is still needed. |
| `backend/mocks/fixtures/` | Add the NYC school fixture for case 2. |
| Tests | Add: Buffalo is stopped, New Jersey is stopped, each of the five boroughs passes. |

## Open question for Justin and Mara

**Far Rockaway (Queens) is served by PSEG Long Island, not Con Edison.** Do we support it, or stop it as out of scope? Until decided, the plan assumes Con Edison for every NYC building and flags the utility for the user to confirm.
