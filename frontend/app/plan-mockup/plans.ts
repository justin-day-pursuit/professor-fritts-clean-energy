/**
 * The saved demos the mockup pages show, built from data/plans.json.
 *
 * plans.json is written by `python manage.py export_plan_summaries --out ../frontend/app/plan-mockup/data`, which replays
 * each saved real run for free. Nothing here calls the backend or Claude. To show a newly recorded case, add it to the
 * backend's replay menu and run the export again.
 */
import raw from "./data/plans.json";
import type { Outcome, PlanFile, PlanSummary } from "./plan-types";

/** One saved demo, ready for the pages. */
export interface PlanView {
  id: string;
  label: string;
  kind: "recorded" | "scripted";
  tag: string;
  question: string;
  status: string;
  /** What the user typed or what we pre-filled: address, budget, goal and so on. */
  profile: Record<string, string | number | null>;
  /** The tools the run used, in the order it first used each one (drives the "working" narration). */
  tools: string[];
  outcome: Outcome;
  plan: PlanSummary;
  markdown: string;
}

const files = (raw as unknown as PlanFile[]).filter((p) => p.plan_summary);

/** The order the sample plans are shown in on every page: the home page cards, the sample pills and "Try another building". */
const SHOW_ORDER = [
  "plan_red_hook_rec_center",
  "plan_jefferson_market_library",
  "plan_ps236_bronx",
  "plan_ps38_staten_island",
  "plan_ps24_bronx_existing_solar",
];

/** A plan's place in SHOW_ORDER; a plan not listed there goes to the end, in the order it was exported. */
const place = (id: string) => (SHOW_ORDER.includes(id) ? SHOW_ORDER.indexOf(id) : SHOW_ORDER.length);

export const PLANS: PlanView[] = files.map((f) => {
  const plan = f.plan_summary as PlanSummary;
  return {
    id: f.id,
    label: f.label,
    kind: f.kind,
    tag: f.tag,
    question: f.question,
    status: f.status,
    profile: { ...(plan.building.intake as Record<string, string | number | null>), ...f.intake },
    tools: plan.tools.map((t) => t.tool),
    outcome: plan.outcome,
    plan,
    markdown: f.markdown ?? "",
  };
}).sort((a, b) => place(a.id) - place(b.id));
