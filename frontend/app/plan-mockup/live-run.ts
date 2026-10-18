/**
 * Running the real planner from the design page.
 *
 * When a visitor types their own address and presses Run, the page sends what they entered to the backend agent, the same
 * agent the classic planner uses. This file holds the pieces of that, kept apart from the page so each can be tested alone:
 *  - turning the form into the profile the agent reads, and the question it is asked,
 *  - checking what is still missing before a run is worth starting,
 *  - starting the run in the background and asking for its progress until it finishes,
 *  - turning the agent's steps into the plain sentences Fritts says, and the finished run into a plan the report screen shows.
 *
 * A real run uses Claude credits, so nothing here starts one on its own: it only happens when the visitor presses Run.
 */
import { ApiError, createSession, getLatestRun, startRun, uploadDocument } from "@/lib/api";
import type { RunEventResponse, RunResponse } from "@/lib/types";
import { buildingTypeLabel, numberOf, type FoundBuilding } from "./address";
import type { PlanSummary } from "./plan-types";
import type { PlanView } from "./plans";

// ---------------------------------------------------------------------------------------------- what the visitor typed

/** The boxes on the form that the visitor can type in. Everything is text, exactly as typed, until a run is started. */
export type RunForm = Partial<
  Record<
    "annual_kwh" | "budget_amount" | "goal" | "critical_loads" | "roof_area_sqft" | "roof_type" | "existing_solar_kw" | "existing_renewables" | "existing_efficiency",
    string
  >
>;

/** A dollar amount written the way people write it ("$400k", "1.2 million", "800,000") as a number, or null. */
export function parseMoney(text: string | undefined): number | null {
  if (!text) return null;
  const match = text.toLowerCase().replace(/,/g, "").match(/(\d+(?:\.\d+)?)\s*(k|m|million|thousand)?/);
  if (!match) return null;
  const value = Number(match[1]);
  const unit = match[2];
  const scaled = unit === "k" || unit === "thousand" ? value * 1_000 : unit === "m" || unit === "million" ? value * 1_000_000 : value;
  return scaled > 0 ? Math.round(scaled) : null;
}

/** A plain number with commas allowed ("456,834"), or null. */
export function parseNumber(text: string | undefined): number | null {
  if (!text) return null;
  const value = Number(text.replace(/[,\s]/g, ""));
  return Number.isFinite(value) && value > 0 ? value : null;
}

/** The percent and the year in a goal sentence like "cut grid electricity 30% by 2030". Either can be missing. */
export function parseGoal(text: string | undefined): { percent: number | null; year: number | null } {
  const percent = text?.match(/(\d{1,3})\s*%/);
  const year = text?.match(/\b(20\d{2})\b/);
  return { percent: percent ? Number(percent[1]) : null, year: year ? Number(year[1]) : null };
}

/** The profile the agent reads, built from the building the city's records found and what the visitor typed. */
export function buildProfile(found: FoundBuilding, form: RunForm): Record<string, string | number> {
  const record = found.record;
  const goal = parseGoal(form.goal);
  const profile: Record<string, string | number | null> = {
    city: "New York",
    state: "NY",
    address: found.label.split(",")[0].trim(),
    borough: found.borough,
    building_name: found.label,
    building_type: buildingTypeLabel(record).toLowerCase(),
    utility: "Con Edison",
    floor_area_sqft: numberOf(record?.bldgarea),
    year_built: numberOf(record?.yearbuilt),
    annual_kwh: parseNumber(form.annual_kwh),
    budget_amount: parseMoney(form.budget_amount),
    budget_type: "capital",
    goal: form.goal?.trim() || null,
    goal_percent: goal.percent,
    target_year: goal.year,
    critical_loads: form.critical_loads?.trim() || null,
    roof_area_sqft: parseNumber(form.roof_area_sqft),
    roof_type: form.roof_type?.trim() || null,
    existing_solar_kw: parseNumber(form.existing_solar_kw),
    existing_renewables: form.existing_renewables?.trim() || "none",
    existing_efficiency: form.existing_efficiency?.trim() || "none",
  };
  // Leave out anything that was not given, so the agent sees a blank, not a made-up zero.
  return Object.fromEntries(Object.entries(profile).filter(([, value]) => value !== null && value !== "")) as Record<string, string | number>;
}

/** The question the agent is asked, in the visitor's own terms. */
export function buildQuestion(form: RunForm): string {
  const goal = parseGoal(form.goal);
  const budget = parseMoney(form.budget_amount);
  const target = form.goal?.trim()
    ? goal.percent
      ? `cut grid power ${goal.percent}%${goal.year ? ` by ${goal.year}` : ""}`
      : form.goal.trim().replace(/[.?!]+$/, "").toLowerCase()
    : "cut grid power";
  const money = budget ? ` on a $${budget.toLocaleString("en-US")} capital budget` : "";
  const outage = form.critical_loads?.trim() ? ` and keep ${form.critical_loads.trim().replace(/[.?!]+$/, "")} running during outages` : "";
  return `How can we ${target}${outage}${money}?`;
}

/** What the agent cannot start without, in the visitor's words. An empty list means a run can begin. */
export function missingForRun(found: FoundBuilding | null, form: RunForm): string[] {
  const missing: string[] = [];
  if (!found?.borough) missing.push("address");
  if (parseMoney(form.budget_amount) === null) missing.push("capital budget");
  if (!form.goal?.trim()) missing.push("energy goal");
  return missing;
}

// ------------------------------------------------------------------------------------------------ the steps, in words

/** Friendly narration for each tool the run uses, in the order the run first used it. */
export const NARRATION: Record<string, string> = {
  get_building_profile: "Reading your building details",
  lookup_ny_building_records: "Checking NYC city records for your lot",
  calculate: "Running the numbers",
  get_solar_production: "Estimating rooftop solar with PVWatts",
  get_utility_rates: "Looking up Con Edison electricity prices",
  get_utility_tariff: "Matching your electricity tariff",
  optimize_solar_storage: "Sizing a backup battery",
  search_ny_incentives_and_rules: "Checking incentives and NYC rules",
  get_hazard_context: "Checking flood and heat risk",
  run_financial_model: "Costing the three scenarios",
};

/** The two steps every run ends with. */
export const CLOSING_STEPS = ["Checking every number has a label and a source", "Writing your plan"];

/** The sentences for a list of tools, each once, in order, then the closing steps. Used for saved plans, whose tools are known. */
export function narrationFor(tools: string[]): string[] {
  const seen: string[] = [];
  for (const tool of tools) {
    const line = NARRATION[tool];
    if (line && !seen.includes(line)) seen.push(line);
  }
  return [...seen, ...CLOSING_STEPS];
}

/** The first thing shown before the agent has taken a step. */
export const FIRST_STEP = NARRATION.get_building_profile;

/**
 * The steps of a run still in progress, from the events it has recorded so far. Each tool the agent has called shows once,
 * in order; when it starts writing the roadmap the two closing steps are added. The last line is the one being worked on.
 */
export function stepsSoFar(events: RunEventResponse[]): string[] {
  const tools: string[] = [];
  let writing = false;
  for (const event of events) {
    if (event.kind !== "tool_call") continue;
    const tool = String(event.payload.tool ?? "");
    if (tool === "write_roadmap") writing = true;
    else if (NARRATION[tool] && !tools.includes(tool)) tools.push(tool);
  }
  const lines = tools.map((tool) => NARRATION[tool]);
  if (writing) lines.push(...CLOSING_STEPS);
  return lines.length ? lines : [FIRST_STEP];
}

// -------------------------------------------------------------------------------------------- a finished run, as a plan

/** The saved-plan shape the report screen shows, built from a finished run. Returns null if the run has no plan. */
export function planFromRun(run: RunResponse, question: string): PlanView | null {
  const plan = (run.output as { plan_summary?: PlanSummary }).plan_summary;
  if (!plan) return null;
  const intake = plan.building.intake as Record<string, string | number | null>;
  return {
    id: `live-${run.id}`,
    label: String(intake.building_name ?? "Your building"),
    kind: "recorded",
    tag: "",
    question,
    status: run.status,
    profile: { ...intake },
    tools: plan.tools.map((t) => t.tool),
    outcome: plan.outcome,
    plan,
    markdown: String((run.output as { markdown?: string }).markdown ?? ""),
  };
}

// ---------------------------------------------------------------------------------------------------- talking to the agent

/** Why a live run did not give a plan, in a form the page can show. */
export type LiveFailure = "limit" | "unreachable" | "needs_input" | "failed" | "timeout";

/** A live run that did not finish with a plan. `message` is a plain sentence the visitor can read. */
export class LiveRunError extends Error {
  kind: LiveFailure;

  constructor(kind: LiveFailure, message: string) {
    super(message);
    this.name = "LiveRunError";
    this.kind = kind;
  }
}

/** How often the page asks for progress, how many failed asks in a row it forgives, and when it gives up (milliseconds). */
export const POLL_EVERY_MS = 2_500;
const FORGIVEN_MISSES = 5;
const GIVE_UP_AFTER_MS = 15 * 60 * 1000;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Starts a real run and waits for it, calling `onProgress` with each look at the run so the page can show the real steps.
 * Resolves with the finished run (status done or partial, with a plan). Throws a LiveRunError otherwise.
 * `wait` and `now` can be replaced, which is how it is tested without real waiting.
 */
export async function runLive(
  profile: Record<string, string | number>,
  question: string,
  onProgress: (run: RunResponse) => void,
  options: { wait?: (ms: number) => Promise<unknown>; now?: () => number; isCancelled?: () => boolean; bill?: File | null } = {},
): Promise<RunResponse> {
  const wait = options.wait ?? sleep;
  const now = options.now ?? Date.now;
  const cancelled = options.isCancelled ?? (() => false);

  let sessionId: string;
  try {
    sessionId = (await createSession({ profile })).id;
    // An attached bill goes first, so the run can use it. If it cannot be saved, the run still goes ahead without it.
    if (options.bill) await uploadDocument(sessionId, options.bill).catch(() => undefined);
    await startRun(sessionId, { content: question });
  } catch (error) {
    if (error instanceof ApiError && error.status === 429) throw new LiveRunError("limit", error.message);
    if (error instanceof ApiError) throw new LiveRunError("failed", "The planner could not start your analysis just now. Please try again in a moment.");
    throw new LiveRunError("unreachable", "I couldn't reach the planner just now. Please try again in a moment, or open one of the sample plans.");
  }

  const started = now();
  let misses = 0;
  while (now() - started < GIVE_UP_AFTER_MS) {
    if (cancelled()) throw new LiveRunError("failed", "Stopped.");
    await wait(POLL_EVERY_MS);
    let run: RunResponse;
    try {
      run = await getLatestRun(sessionId);
      misses = 0;
    } catch (error) {
      // The run may not exist yet (404), or the connection blinked: ask again, but not forever.
      if (error instanceof ApiError && error.status === 404) continue;
      misses += 1;
      if (misses >= FORGIVEN_MISSES) throw new LiveRunError("unreachable", "I lost touch with the planner while it was working. Please try again.");
      continue;
    }
    onProgress(run);
    if (run.status === "queued" || run.status === "running") continue;
    if (run.status === "needs_input") {
      const question = String((run.output as { question?: string }).question ?? "I need a little more information to start.");
      throw new LiveRunError("needs_input", question);
    }
    if (run.status === "done" || run.status === "partial") return run;
    const reason = String((run.output as { error?: string }).error ?? "");
    throw new LiveRunError("failed", reason || "The analysis did not finish. Please try again.");
  }
  throw new LiveRunError("timeout", "This is taking longer than expected. Please try again in a few minutes.");
}
