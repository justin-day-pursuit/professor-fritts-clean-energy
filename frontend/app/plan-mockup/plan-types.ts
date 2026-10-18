/**
 * Types for the plan summary that the backend writes with every run (output.plan_summary), plus the saved-demo file
 * the design pages read (data/plans.json, written by `manage.py export_plan_summaries`).
 *
 * Raw tool data (city records, PVWatts, rates, hazards, and so on) is typed loosely on purpose: the screen shows
 * every field it finds, so a new field the backend adds appears without a front-end change.
 */

export type Range = [number, number];
export type Json = Record<string, unknown>;

export interface Outcome {
  code: string;
  label: string;
  tone: "good" | "caution" | "next-step";
  headline: string;
  subhead: string;
  recommended: string | null;
}

export interface CostItem {
  item: string;
  basis: string;
  usd: Range;
  /** The best guess for this line: the median price of similar NYC projects. */
  usd_best?: number;
}

export interface Scenario {
  calc_id: string;
  scenario_id: "A" | "B" | "C";
  scenario_name: string;
  goal_pct: number;
  package: { efficiency_level: string; solar_kw_dc: number; battery_kwh: number };
  cost_items: CostItem[];
  upfront_usd: Range;
  /** The best guess for the upfront cost, with upfront_usd as the typical range around it. */
  upfront_usd_best?: number;
  net_cost_usd_best?: number;
  payback_years_best?: number | null;
  incentives_counted_usd: Range;
  net_cost_usd: Range;
  reduction_kwh: Range;
  reduction_pct_of_use: Range;
  share_of_goal_pct: Range;
  reaches_goal: boolean;
  surplus_solar_kwh: Range;
  surplus_not_counted_in_savings: boolean;
  budget_gap_usd: Range | null;
  budget_note: string;
  annual_savings_usd: Range;
  payback_years: Range | null;
  budget_strain: string;
  budget_ratio: Range | null;
  outage_hours: Range;
  solar_alone_pct_of_use: Range;
  solar_alone_exceeds_use: boolean;
  assumption_text?: string;
  [key: string]: unknown;
}

export interface Claim {
  text: string;
  label: "FACT" | "ESTIMATE" | "ASSUMPTION" | "RECOMMENDATION";
  confidence: "high" | "medium" | "low";
  source_url?: string | null;
  calc_id?: string | null;
  assumption_id?: string | null;
  value_low?: number | null;
  value_high?: number | null;
  units?: string | null;
}

export interface Section {
  section_id: string;
  title: string;
  claims: Claim[];
  stand_in_note?: string | null;
}

export interface ToolRecord {
  tool: string;
  mock: boolean | null;
  source_url: string | null;
  retrieved_at: string | null;
  dataset_version: string | null;
  flags: string[];
}

export interface Program {
  name: string;
  status: string;
  status_note?: string;
  deadline?: string;
  quote?: string;
  source_url: string;
  statute_url?: string;
  retrieved_at?: string;
  [key: string]: unknown;
}

export interface PlanSummary {
  version: number;
  /** The agent's plain-words answer to the question, shown under the headline. Absent on plans recorded before it existed. */
  plain_answer?: string | null;
  outcome: Outcome;
  building: { intake: Json; city_records: Json; energy_report: Json | null; roof_assessment: Json | null; site_context: Json };
  baseline: { annual_kwh: number | null; source: string; goal_percent: number | null; goal_kwh: number | null };
  solar: { production: (Json & { data?: Json }) | null };
  prices: { electricity: Json | null; tariff: Json | null };
  scenarios: Scenario[];
  /** Costs the totals leave out, such as replacing an old roof. */
  not_included: { item: string; why: string; next: string; rough_guide_usd?: Range; basis?: string; sources?: { label: string; url: string }[] }[];
  cost_basis: Json;
  incentives: Program[];
  battery: Json | null;
  hazards: Json | null;
  calculations: Record<string, Json>;
  /** Plain names for each calculation id (C1, F-B, ...), and a plain sentence for each flag the tools can raise. */
  calculation_names: Record<string, string>;
  flag_text: Record<string, string>;
  confirm_first: { kind: string; text: string }[];
  assumptions: { id: string; text: string }[];
  referrals: Claim[];
  next_steps: { name: string; url: string; why: string; contact: string }[];
  sources: { label: string; url: string; retrieved_at: string; sample: boolean }[];
  sections: Section[];
  flags: string[];
  tools: ToolRecord[];
  usage: Json | null;
}

/** One saved demo as the export writes it. */
export interface PlanFile {
  id: string;
  label: string;
  kind: "recorded" | "scripted";
  tag: string;
  question: string;
  status: "done" | "partial" | string;
  intake: Record<string, string | number | null>;
  plan_summary: PlanSummary | null;
  markdown: string | null;
}
