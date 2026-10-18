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
});
