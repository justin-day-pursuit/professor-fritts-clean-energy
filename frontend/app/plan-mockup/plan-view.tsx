/**
 * The results page of the /plan-mockup design: one saved real run, shown in full and in plain language.
 *
 * Order: the short answer, how to read the plan, what to confirm first, the three plans, the roadmap, the professionals to
 * call, incentives, who to contact, how sure we are, then "all the data we found" (every record, price, calculation and tool
 * result the run produced) and the full report with every labeled statement. Nothing the run found is left off the page, but
 * code-style names (field names, flag names, calculation ids, tool names) appear only in the "Developer view".
 */
"use client";

import { createContext, useContext, useState, type ReactNode, type SyntheticEvent } from "react";
import { SAMPLE_BADGE_TEXT } from "./copy";
import type { Claim, PlanSummary, Program, Scenario, Section } from "./plan-types";
import { fieldLabel, fieldValue, isInternalField, plainify, toolLabel } from "./plain";
import { copyShareLink, downloadPlanPdf, shortLink } from "./plan-actions";
import type { PlanView } from "./plans";
import {
  Card,
  Chip,
  LABELS,
  RangeBar,
  SectionTitle,
  LinkedText,
  SourceLink,
  hoursRange,
  isWeb,
  money,
  moneyExact,
  moneyRange,
  moneyRangeExact,
  nice,
  pctRange,
  show,
  yearsRange,
} from "./ui";

type Obj = Record<string, unknown>;
const obj = (x: unknown): Obj => (x && typeof x === "object" && !Array.isArray(x) ? (x as Obj) : {});

const SCENARIO_NAME: Record<string, string> = { A: "Efficiency only", B: "Efficiency + solar", C: "Efficiency, solar + backup power" };

/** Plain names the page needs from the summary: calculation names and flag sentences, plus the developer-view switch. */
interface PlainContext {
  dev: boolean;
  calcNames: Record<string, string>;
  flagText: Record<string, string>;
}
const PlainCtx = createContext<PlainContext>({ dev: false, calcNames: {}, flagText: {} });

/** The section titles as a reader would say them. */
const SECTION_NAME: Record<string, string> = {
  "3": "Assumptions behind the numbers",
  "12": "What is uncertain, and what would help",
  "13": "Sources",
};

// ------------------------------------------------------------------------------------------------- pieces

/** Every field of a record as a plain label and a value, so a new field from the backend still shows up. */
function KV({ data, skip = [] }: { data: Obj; skip?: string[] }) {
  const { dev } = useContext(PlainCtx);
  const rows = Object.entries(data).filter(([k]) => !skip.includes(k) && !k.startsWith("_") && (dev || !isInternalField(k)));
  if (rows.length === 0) return <p className="text-sm text-[var(--fr-mute)]">Nothing recorded.</p>;
  return (
    <dl className="grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-[minmax(0,15rem)_1fr]">
      {rows.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="text-[var(--fr-mute)]">
            {fieldLabel(k)}
            {dev && <span className="ml-1 font-mono text-[10px] text-[var(--fr-warn)]">{k}</span>}
          </dt>
          <dd className="break-words text-[var(--fr-ink)]">
            {isWeb(v) ? <SourceLink url={v}>link</SourceLink> : v && typeof v === "object" && !Array.isArray(v) ? <KV data={obj(v)} /> : dev ? fieldValue(k, v) : plainify(fieldValue(k, v))}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** True inside a report section that is open: the drop-downs within it then open too. */
const OpenCtx = createContext(false);

/**
 * A drop-down. Left alone it follows its section: closed when the section is closed, open when the section is open. A report
 * section passes `open` and `onToggle` itself, so the page can keep only one section open at a time.
 */
function Detail({ title, note, children, open, onToggle }: { title: string; note?: string; children: ReactNode; open?: boolean; onToggle?: (e: SyntheticEvent<HTMLDetailsElement>) => void }) {
  const inherited = useContext(OpenCtx);
  return (
    <details open={open ?? inherited} onToggle={onToggle} className="rounded-xl border border-[var(--fr-line)] bg-white p-4">
      <summary className="cursor-pointer font-semibold text-[var(--fr-ink)]">
        {title}
        {note && <span className="ml-2 text-xs font-normal text-[var(--fr-mute)]">{note}</span>}
      </summary>
      <div className="mt-3 space-y-3">{children}</div>
    </details>
  );
}

/** Where a block of data came from: live or a saved sample, when it was read, a link, and any caveats in plain sentences. */
function ToolMeta({ payload }: { payload: Obj }) {
  const { dev, flagText } = useContext(PlainCtx);
  const mock = payload.mock === true;
  const flags = Array.isArray(payload.flags) ? (payload.flags as string[]) : [];
  const caveats = flags.map((f) => flagText[f] ?? (dev ? f : "")).filter(Boolean);
  return (
    <div className="space-y-1.5 text-xs text-[var(--fr-mute)]">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 font-bold text-white ${mock ? "bg-[#b7791f]" : "bg-[var(--fr-teal)]"}`}>{mock ? SAMPLE_BADGE_TEXT : "Live data"}</span>
        {typeof payload.retrieved_at === "string" && payload.retrieved_at && <span>read {payload.retrieved_at.slice(0, 10)}</span>}
        {dev && typeof payload.dataset_version === "string" && <span className="font-mono text-[var(--fr-warn)]">{payload.dataset_version}</span>}
        <SourceLink url={payload.source_url} />
      </div>
      {caveats.map((c) => (
        <p key={c} className="text-[var(--fr-ink)]/80">• {c}</p>
      ))}
    </div>
  );
}

function ToolBlock({ title, payload, skip }: { title: string; payload: Obj | null; skip?: string[] }) {
  if (!payload) return null;
  return (
    <Detail title={title}>
      <ToolMeta payload={payload} />
      <KV data={obj(payload.data)} skip={skip} />
    </Detail>
  );
}

/** What each of the four labels means, with an example and what the reader should do about it. */
const LABEL_EXPLAINED: Record<string, { meaning: string; example: string; action: string }> = {
  FACT: {
    meaning: "From a named source.",
    example: "The size of the roof, from the city's roof check.",
    action: "Trust it. The source is linked so you can look.",
  },
  ESTIMATE: {
    meaning: "Calculated from the building's data, and always shown as a range.",
    example: "How much grid electricity a plan would cut.",
    action: "Use it to compare the plans. Expect it to move once an audit and contractor bids are in.",
  },
  ASSUMPTION: {
    meaning: "A starting point used because the real number isn't known.",
    example: "The state-average electricity price, or the savings percent for efficiency work.",
    action: "Check it. You can change it: enter your own electricity price and the plan changes to match. The efficiency savings percent stays a planning estimate until an energy audit.",
  },
  RECOMMENDATION: {
    meaning: "A suggested next step.",
    example: "Have a roofer look at the roof before any panels are ordered.",
    action: "Take it to the professional it names. They make the final call.",
  },
};

/** One labeled statement from the report, with what it was worked out from and where it came from. */
function ClaimRow({ claim }: { claim: Claim }) {
  const { dev, calcNames } = useContext(PlainCtx);
  const range = claim.value_low != null && claim.value_high != null ? `${show(claim.value_low)}${claim.value_low !== claim.value_high ? ` to ${show(claim.value_high)}` : ""} ${claim.units ?? ""}` : "";
  // The first sentence is the bold headline; any further sentences are the lighter reasoning under it.
  const text = dev ? claim.text : plainify(claim.text);
  const sentences = text.split(/(?<=[.!?])\s+(?=[A-Z$(])/);
  const headline = sentences[0];
  const reasoning = sentences.slice(1).join(" ");
  // A box keeps its reasoning to a few lines so the boxes in a row stay the same size; "Read more" opens the rest.
  const [expanded, setExpanded] = useState(false);
  const long = reasoning.length > 150;
  return (
    <li className="flex flex-col gap-1.5 rounded-xl border border-[var(--fr-line)] bg-white p-3.5 text-sm">
      <p className="text-[15px] font-semibold leading-snug text-[var(--fr-ink)]">{headline}</p>
      {reasoning && <p className={`text-[13.5px] text-[var(--fr-mute)] ${long && !expanded ? "line-clamp-3" : ""}`}>{reasoning}</p>}
      {long && (
        <button type="button" onClick={() => setExpanded(!expanded)} className="w-fit text-xs text-[var(--fr-teal)] underline underline-offset-2">
          {expanded ? "Show less" : "Read more"}
        </button>
      )}
      {range && <p className="text-xs text-[var(--fr-mute)]">{range.trim()}</p>}
      <div className="mt-auto flex flex-wrap items-center gap-x-2.5 gap-y-1 border-t border-[var(--fr-line)] pt-2 text-xs text-[var(--fr-mute)]">
        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-[var(--fr-ink)]">
          <i className="inline-block h-2 w-2 rounded-full" style={{ background: LABELS[claim.label]?.color ?? "#555" }} />
          {claim.label}
        </span>
        <span>{claim.confidence} confidence</span>
        {claim.calc_id && <span>From: {calcNames[claim.calc_id] ?? claim.calc_id}</span>}
        {dev && claim.assumption_id && <span className="font-mono text-[var(--fr-warn)]">{claim.assumption_id}</span>}
        {dev && claim.calc_id && <span className="font-mono text-[var(--fr-warn)]">{claim.calc_id}</span>}
        <SourceLink url={claim.source_url} />
      </div>
    </li>
  );
}

// ---------------------------------------------------------------------------------------------- scenarios

function ScenarioCard({ id, s, budget, recommended, reason }: { id: "A" | "B" | "C"; s?: Scenario; budget: number; recommended: boolean; reason: string }) {
  const { dev } = useContext(PlainCtx);
  if (!s) {
    return (
      <Card className="border-dashed bg-[var(--fr-soft)]">
        <div className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">Plan {id}</div>
        <div className="text-lg font-semibold text-[var(--fr-ink)]">{SCENARIO_NAME[id]}</div>
        <p className="mt-3 text-sm text-[var(--fr-mute)]">Not costed in this plan.</p>
        <p className="mt-1 text-sm text-[var(--fr-ink)]">{reason}</p>
      </Card>
    );
  }
  const over = s.budget_strain === "over budget" && s.budget_gap_usd;
  const costMax = Math.max(s.upfront_usd[1], budget) * 1.08;
  const goal = s.goal_pct ?? 30;
  return (
    <Card className={recommended ? "ring-2 ring-[var(--fr-gold)]" : ""}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">Plan {id}{dev && <span className="ml-1 font-mono text-[var(--fr-warn)]">{s.calc_id}</span>}</div>
          <div className="text-lg font-semibold text-[var(--fr-ink)]">{SCENARIO_NAME[id]}</div>
        </div>
        {recommended ? (
          <span className="rounded-full bg-[var(--fr-gold)] px-2.5 py-1 text-[11px] font-bold text-[var(--fr-ink)]">Recommended</span>
        ) : over ? (
          <span className="rounded-full bg-[#fbe3d9] px-2.5 py-1 text-[11px] font-bold text-[var(--fr-warn)]">Over budget</span>
        ) : (
          <span className="rounded-full bg-[#dff3ea] px-2.5 py-1 text-[11px] font-bold text-[var(--fr-ink)]">{s.budget_strain === "within budget" ? "Fits budget" : "May exceed budget"}</span>
        )}
      </div>
      <p className="mt-1 text-xs text-[var(--fr-mute)]">
        {s.package.efficiency_level === "standard" ? "Standard efficiency (lighting and controls)" : s.package.efficiency_level === "deep" ? "Expanded efficiency (lighting, controls and building systems)" : ""}
        {s.package.solar_kw_dc > 0 && ` · ${s.package.solar_kw_dc} kW of solar panels`}
        {s.package.battery_kwh > 0 && ` · ${s.package.battery_kwh} kWh battery`}
      </p>

      <div className="mt-4">
        <div className="flex items-baseline justify-between text-sm"><span className="text-[var(--fr-mute)]">Cuts grid electricity</span><span className="font-semibold text-[var(--fr-ink)]">{pctRange(s.reduction_pct_of_use)}</span></div>
        <RangeBar low={s.reduction_pct_of_use[0]} high={s.reduction_pct_of_use[1]} max={100} color={s.reaches_goal ? "#1c8c7e" : "#b7791f"} marker={goal} markerLabel={`${goal}% goal`} />
        <p className="mt-1 text-xs text-[var(--fr-mute)]">{s.reaches_goal ? "Reaches your goal even at the low end." : `Doesn't reach ${goal}% at the low end.`} That is {show(s.reduction_kwh[0])} to {show(s.reduction_kwh[1])} kWh a year.</p>
      </div>

      <div className="mt-4">
        <div className="flex items-baseline justify-between text-sm"><span className="text-[var(--fr-mute)]">Upfront cost</span><span className="font-semibold text-[var(--fr-ink)]">{moneyRange(s.upfront_usd)}</span></div>
        <RangeBar low={s.upfront_usd[0]} high={s.upfront_usd[1]} max={costMax} color={over ? "#c2562b" : "#2f6fb5"} marker={budget} markerLabel={`Budget ${money(budget)}`} />
        {s.upfront_usd_best != null && <p className="mt-1 text-xs text-[var(--fr-mute)]">Median of similar NYC projects: about {money(s.upfront_usd_best)}</p>}
        {over ? <p className="mt-1 text-xs font-medium text-[var(--fr-warn)]">{moneyRange(s.budget_gap_usd as [number, number])} more than your budget</p> : null}
        {s.incentives_counted_usd[1] > 0 && <p className="mt-1 text-xs text-[var(--fr-mute)]">After a {moneyRange(s.incentives_counted_usd)} federal credit: {moneyRange(s.net_cost_usd)}</p>}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--fr-line)] pt-3 text-sm">
        <div><dt className="text-xs text-[var(--fr-mute)]">Saves each year</dt><dd className="font-semibold text-[var(--fr-ink)]">{moneyRange(s.annual_savings_usd)}</dd></div>
        <div><dt className="text-xs text-[var(--fr-mute)]">Pays back in</dt><dd className="font-semibold text-[var(--fr-ink)]">{yearsRange(s.payback_years)}</dd>{s.payback_years_best ? <dd className="text-[11px] text-[var(--fr-mute)]">about {Math.round(s.payback_years_best)} years at the median cost</dd> : null}</div>
        <div><dt className="text-xs text-[var(--fr-mute)]">Backup power</dt><dd className="font-semibold text-[var(--fr-ink)]">{hoursRange(s.outage_hours)}</dd></div>
        <div><dt className="text-xs text-[var(--fr-mute)]">Portion of your goal met</dt><dd className="font-semibold text-[var(--fr-ink)]">{pctRange(s.share_of_goal_pct)}</dd></div>
      </dl>
      {s.budget_note && <p className="mt-3 text-xs text-[var(--fr-mute)]">{s.budget_note}</p>}
      {s.surplus_solar_kwh[1] > 0 && <p className="mt-3 rounded-lg bg-[var(--fr-soft)] p-2 text-xs text-[var(--fr-mute)]">This roof could make more power than the building uses ({show(s.surplus_solar_kwh[0])} to {show(s.surplus_solar_kwh[1])} kWh extra). The extra isn&rsquo;t counted as savings.</p>}

      <details className="mt-3 rounded-lg border border-[var(--fr-line)] p-3">
        <summary className="cursor-pointer text-sm font-semibold text-[var(--fr-ink)]">Itemized bill</summary>
        <table className="mt-2 w-full text-left text-xs">
          <thead><tr className="text-[var(--fr-mute)]"><th className="py-1 pr-2">Item</th><th className="py-1 pr-2">Typical range</th><th className="py-1 pr-2">Median of similar projects</th></tr></thead>
          <tbody>
            {s.cost_items.map((c) => (
              <tr key={c.item} className="border-t border-[var(--fr-line)] align-top">
                <td className="py-1.5 pr-2"><div className="font-medium text-[var(--fr-ink)]">{c.item}</div><div className="text-[var(--fr-mute)]"><LinkedText text={dev ? c.basis : plainify(c.basis)} /></div></td>
                <td className="whitespace-nowrap py-1.5 pr-2 text-[var(--fr-ink)]">{moneyRangeExact(c.usd)}</td>
                <td className="whitespace-nowrap py-1.5 pr-2 text-[var(--fr-mute)]">{c.usd_best != null ? moneyExact(c.usd_best) : ""}</td>
              </tr>
            ))}
            <tr className="border-t-2 border-[var(--fr-ink)] font-semibold"><td className="py-1.5 pr-2">Upfront total</td><td className="py-1.5 pr-2 text-[var(--fr-ink)]">{moneyRangeExact(s.upfront_usd)}</td><td className="py-1.5 text-[var(--fr-mute)]">{s.upfront_usd_best != null ? moneyExact(s.upfront_usd_best) : ""}</td></tr>
            <tr className="font-semibold"><td className="py-1.5 pr-2">Net after incentives counted</td><td className="py-1.5 pr-2 text-[var(--fr-ink)]">{moneyRangeExact(s.net_cost_usd)}</td><td className="py-1.5 text-[var(--fr-mute)]">{s.net_cost_usd_best != null ? moneyExact(s.net_cost_usd_best) : ""}</td></tr>
          </tbody>
        </table>
      </details>
    </Card>
  );
}

// ------------------------------------------------------------------------------------------------ incentives

// ----------------------------------------------------------------------------------------- side-by-side tables

const PLAN_IDS = ["A", "B", "C"] as const;
const th = "px-3 py-2.5 text-left align-top";
const rowHead = "px-3 py-2.5 text-left align-top font-semibold text-[var(--fr-ink)] w-[22%]";

/** The plan's make-up in a few words, for the column heading. */
function packageText(s?: Scenario): string {
  if (!s) return "Not costed";
  const parts = [s.package.efficiency_level === "deep" ? "Expanded efficiency" : "Standard efficiency"];
  if (s.package.solar_kw_dc > 0) parts.push(`solar (${s.package.solar_kw_dc} kW)`);
  if (s.package.battery_kwh > 0) parts.push(`${s.package.battery_kwh} kWh battery`);
  return parts.join(" + ");
}

/**
 * The one plan a statement is about, from the plan letters in its own words ("Scenario B ...", "Plan C ...", "(A)"). A statement
 * that names several plans, or none, is about all of them and is shown below the table instead.
 */
function planOf(claim: Claim): "A" | "B" | "C" | null {
  const letters = new Set<string>();
  for (const m of claim.text.matchAll(/\b(?:Scenarios?|Plans?)\s+([ABC])\b|\(([ABC])\)|\bfor\s+([ABC])\b/g)) letters.add(m[1] ?? m[2] ?? m[3]);
  return letters.size === 1 ? ([...letters][0] as "A" | "B" | "C") : null;
}

/** A statement inside a table cell: the sentence, a tag only when it is not an estimate, and its source. */
function CellNote({ claim }: { claim: Claim }) {
  const { dev, calcNames } = useContext(PlainCtx);
  return (
    <li className="space-y-0.5">
      <p className="text-[var(--fr-ink)]">{dev ? claim.text : plainify(claim.text)}</p>
      <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-[var(--fr-mute)]">
        {claim.label !== "ESTIMATE" && <Chip label={claim.label} />}
        {claim.calc_id && <span>from: {calcNames[claim.calc_id] ?? claim.calc_id}</span>}
        <SourceLink url={claim.source_url} />
      </div>
    </li>
  );
}

/** Splits a section's statements into those about one plan (by plan) and the rest (general). */
function splitByPlan(claims: Claim[]): { byPlan: Record<string, Claim[]>; general: Claim[] } {
  const byPlan: Record<string, Claim[]> = { A: [], B: [], C: [] };
  const general: Claim[] = [];
  for (const c of claims) {
    const id = planOf(c);
    if (id) byPlan[id].push(c);
    else general.push(c);
  }
  return { byPlan, general };
}

/** The statement rows of a plan table: what the written plan says about each plan, in that plan's column. */
function StatementRow({ byPlan, recommended }: { byPlan: Record<string, Claim[]>; recommended: string | null }) {
  if (PLAN_IDS.every((id) => byPlan[id].length === 0)) return null;
  return (
    <tr className="border-t-2 border-[var(--fr-line)]">
      <th className={rowHead}>What the written plan says</th>
      {PLAN_IDS.map((id) => (
        <td key={id} className={`px-3 py-2.5 align-top text-xs ${recommended === id ? "bg-[var(--fr-soft)]" : ""}`}>
          {byPlan[id].length ? <ul className="space-y-2">{byPlan[id].map((c) => <CellNote key={c.text} claim={c} />)}</ul> : <span className="text-[var(--fr-mute)]">Nothing specific to this plan.</span>}
        </td>
      ))}
    </tr>
  );
}

/** The statements that are about all the plans (or none in particular), shown in full under the table. */
function GeneralStatements({ claims, title }: { claims: Claim[]; title: string }) {
  if (claims.length === 0) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-teal)]">{title}</p>
      <ul className="grid gap-3 sm:grid-cols-2">{claims.map((c) => <ClaimRow key={c.text} claim={c} />)}</ul>
    </div>
  );
}

/** The legend line above a table: one ESTIMATE tag instead of one on every figure. */
function EstimateLegend({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-sm text-[var(--fr-mute)]">
      <Chip label="ESTIMATE" /> <span>{children}</span>
    </div>
  );
}

/** Section 6: the three plans as columns and the questions a reader asks as rows. */
function ComparisonTable({ sum, budget, recommended, claims }: { sum: PlanSummary; budget: number; recommended: string | null; claims: Claim[] }) {
  const { byPlan, general } = splitByPlan(claims);
  const by = (id: string) => sum.scenarios.find((x) => x.scenario_id === id);
  const goal = sum.scenarios[0]?.goal_pct ?? sum.baseline.goal_percent ?? 30;
  const col = (id: string) => (recommended === id ? "bg-[var(--fr-soft)]" : "");
  const cell = (fn: (s: Scenario) => ReactNode) =>
    PLAN_IDS.map((id) => {
      const sc = by(id);
      return <td key={id} className={`px-3 py-2.5 align-top ${col(id)}`}>{sc ? fn(sc) : <span className="text-[var(--fr-mute)]">Not costed in this plan</span>}</td>;
    });
  const goalCell = (s: Scenario) =>
    s.reaches_goal ? (
      <span className="font-semibold text-[#1f7a4d]">Yes, even at the low end</span>
    ) : s.reduction_pct_of_use[1] >= goal ? (
      <span className="font-semibold text-[#9a6a00]">Only at the high end</span>
    ) : (
      <span className="font-semibold text-[var(--fr-warn)]">No</span>
    );
  const budgetCell = (s: Scenario) =>
    s.budget_strain === "within budget" ? (
      <span className="font-semibold text-[#1f7a4d]">Yes{s.budget_ratio ? ` (${Math.round(s.budget_ratio[0] * 100)}% to ${Math.round(s.budget_ratio[1] * 100)}% of it)` : ""}</span>
    ) : (
      <span className="font-semibold text-[var(--fr-warn)]">{s.budget_gap_usd && s.budget_gap_usd[1] > 0 ? `Up to ${money(s.budget_gap_usd[1])} over` : "May exceed it"}</span>
    );
  return (
    <div className="space-y-3">
      <EstimateLegend>Every figure is a calculated range and low confidence. Prices come from similar NYC projects and the state average electricity price, not this building&rsquo;s own bill.</EstimateLegend>
      <div className="overflow-x-auto rounded-xl border border-[var(--fr-line)] bg-white">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="text-[var(--fr-ink)]">
              <th className={th}></th>
              {PLAN_IDS.map((id) => (
                <th key={id} className={`${th} ${col(id)}`}>
                  <div className="text-base font-semibold">Plan {id}{recommended === id ? <span className="ml-2 rounded-full bg-[var(--fr-gold)] px-2 py-0.5 text-[10px] font-bold">Recommended</span> : null}</div>
                  <div className="text-xs font-normal text-[var(--fr-mute)]">{packageText(by(id))}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="[&>tr]:border-t [&>tr]:border-[var(--fr-line)]">
            <tr><th className={rowHead}>Upfront cost</th>{cell((s) => (<><div className="text-base font-bold">{moneyRange(s.upfront_usd)}</div>{s.upfront_usd_best != null && <div className="text-xs text-[var(--fr-mute)]">Median of similar NYC projects: about {money(s.upfront_usd_best)}</div>}</>))}</tr>
            <tr><th className={rowHead}>After the federal credit</th>{cell((s) => (s.incentives_counted_usd[1] > 0 ? <>{moneyRange(s.net_cost_usd)}</> : <span className="text-[var(--fr-mute)]">No credit counted</span>))}</tr>
            <tr><th className={rowHead}>Cuts grid electricity</th>{cell((s) => <>{pctRange(s.reduction_pct_of_use)}</>)}</tr>
            <tr><th className={rowHead}>Reaches the {goal}% goal?</th>{cell(goalCell)}</tr>
            <tr><th className={rowHead}>Saves each year</th>{cell((s) => <>{moneyRange(s.annual_savings_usd)}</>)}</tr>
            <tr><th className={rowHead}>Pays back in</th>{cell((s) => <>{yearsRange(s.payback_years)}</>)}</tr>
            <tr><th className={rowHead}>Backup power</th>{cell((s) => (s.outage_hours[1] > 0 ? <>{hoursRange(s.outage_hours)} for the critical loads</> : <span className="text-[var(--fr-mute)]">None (solar panels shut off in an outage)</span>))}</tr>
            <tr><th className={rowHead}>Fits the {budget ? `$${budget.toLocaleString()} ` : ""}budget?</th>{cell(budgetCell)}</tr>
            <StatementRow byPlan={byPlan} recommended={recommended} />
          </tbody>
        </table>
      </div>
      <GeneralStatements claims={general} title="About all three plans" />
    </div>
  );
}

/** Section 7: each part of the bill as a row, the three plans as columns. */
function CostTable({ sum, recommended, claims }: { sum: PlanSummary; recommended: string | null; claims: Claim[] }) {
  const { byPlan, general } = splitByPlan(claims);
  const by = (id: string) => sum.scenarios.find((x) => x.scenario_id === id);
  const kind = (item: string) => (/efficiency/i.test(item) ? "Efficiency work" : /solar/i.test(item) ? "Rooftop solar" : /battery/i.test(item) ? "Backup battery" : /credit/i.test(item) ? "Federal credit" : item);
  const rows = Array.from(new Set(sum.scenarios.flatMap((s) => s.cost_items.map((c) => kind(c.item)))));
  const col = (id: string) => (recommended === id ? "bg-[var(--fr-soft)]" : "");
  return (
    <div className="space-y-3">
      <EstimateLegend>Each line is a typical range from similar NYC projects, with the median of those projects underneath. None of these costs include replacing the roof.</EstimateLegend>
      <div className="overflow-x-auto rounded-xl border border-[var(--fr-line)] bg-white">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="text-[var(--fr-ink)]">
              <th className={th}></th>
              {PLAN_IDS.map((id) => (
                <th key={id} className={`${th} ${col(id)}`}>
                  <div className="text-base font-semibold">Plan {id}</div>
                  <div className="text-xs font-normal text-[var(--fr-mute)]">{packageText(by(id))}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="[&>tr]:border-t [&>tr]:border-[var(--fr-line)]">
            {rows.map((row) => (
              <tr key={row}>
                <th className={rowHead}>{row}</th>
                {PLAN_IDS.map((id) => {
                  const item = by(id)?.cost_items.find((c) => kind(c.item) === row);
                  return (
                    <td key={id} className={`px-3 py-2.5 align-top ${col(id)}`}>
                      {item ? (
                        <>
                          <div className="font-medium text-[var(--fr-ink)]">{moneyRangeExact(item.usd)}</div>
                          {item.usd_best != null && <div className="text-xs text-[var(--fr-mute)]">Median: {moneyExact(item.usd_best)}</div>}
                          <div className="mt-0.5 text-xs text-[var(--fr-mute)]"><LinkedText text={item.basis} /></div>
                        </>
                      ) : (
                        <span className="text-[var(--fr-mute)]">Not part of this plan</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
            <tr className="border-t-2 border-[var(--fr-ink)] font-semibold">
              <th className={rowHead}>Upfront total</th>
              {PLAN_IDS.map((id) => {
                const sc = by(id);
                return <td key={id} className={`px-3 py-2.5 align-top ${col(id)}`}>{sc ? <><div>{moneyRangeExact(sc.upfront_usd)}</div>{sc.upfront_usd_best != null && <div className="text-xs font-normal text-[var(--fr-mute)]">Median: {moneyExact(sc.upfront_usd_best)}</div>}</> : "Not costed"}</td>;
              })}
            </tr>
            <tr className="font-semibold">
              <th className={rowHead}>After incentives counted</th>
              {PLAN_IDS.map((id) => {
                const sc = by(id);
                return <td key={id} className={`px-3 py-2.5 align-top ${col(id)}`}>{sc ? moneyRangeExact(sc.net_cost_usd) : "Not costed"}</td>;
              })}
            </tr>
            <StatementRow byPlan={byPlan} recommended={recommended} />
          </tbody>
        </table>
      </div>
      <GeneralStatements claims={general} title="Incentives, rules and other cost notes" />
    </div>
  );
}

const STATUS_STYLE: Record<string, { label: string; bg: string }> = {
  open: { label: "Open", bg: "#1c8c7e" },
  uncertain: { label: "Not confirmed", bg: "#b7791f" },
  closed: { label: "Closed", bg: "#5b6b72" },
  rule: { label: "Rule", bg: "#12303d" },
};

function ProgramCard({ p }: { p: Program }) {
  const st = STATUS_STYLE[p.status] ?? { label: nice(p.status), bg: "#555" };
  return (
    <Card>
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className="rounded-full px-2 py-0.5 text-[11px] font-bold text-white" style={{ background: st.bg }}>{st.label}</span>
        {p.retrieved_at && <span className="text-xs text-[var(--fr-mute)]">Read from the official page {p.retrieved_at.slice(0, 10)}</span>}
        {p.deadline && <span className="text-xs text-[var(--fr-mute)]">Deadline {p.deadline}</span>}
      </div>
      <div className="font-semibold text-[var(--fr-ink)]">{p.name}</div>
      {p.status_note && <p className="mt-1 text-sm text-[var(--fr-mute)]">{p.status_note}</p>}
      {p.quote && <blockquote className="mt-2 border-l-4 border-[var(--fr-gold)] pl-3 text-sm italic text-[var(--fr-ink)]">&ldquo;{p.quote}&rdquo;</blockquote>}
      <div className="mt-2 flex gap-3 text-xs">
        <SourceLink url={p.source_url}>Official page</SourceLink>
        <SourceLink url={p.statute_url}>Statute or rule text</SourceLink>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------------------------- the page

/** A price as the plan used it: "$3,131 to $4,668 per kW", with a plain unit for each kind. */
function priceText(kind: string, price: unknown): string {
  const range = (pair: unknown, unit: string) =>
    Array.isArray(pair) && pair.length === 2 ? `$${Number(pair[0]).toLocaleString()} to $${Number(pair[1]).toLocaleString()} ${unit}` : null;
  if (kind === "solar") return range(price, "per kW of panels") ?? show(price);
  if (kind === "battery") return range(price, "per kWh of battery") ?? show(price);
  const p = obj(price);
  const std = range(p.standard, "per kWh saved a year");
  const deep = range(p.deep, "per kWh saved a year");
  return std && deep ? `Standard: ${std}. Expanded: ${deep}.` : show(price);
}

export function Results({ plan, plans, onRestart, onPick }: { plan: PlanView; plans: PlanView[]; onRestart: () => void; onPick: (id: string) => void }) {
  const [dev, setDev] = useState(false);
  // What the Download PDF and Share buttons last did, shown beside them.
  const [note, setNote] = useState("");
  const onDownload = () => {
    setNote("Making your PDF...");
    void downloadPlanPdf(plan.plan).then((r) => setNote(r === "done" ? "PDF downloaded." : r === "unreachable" ? "Couldn't reach the planner. Try printing this page instead." : "The PDF could not be made."));
  };
  // The box under the Share button: the link that was copied, and a button to copy it again.
  const [share, setShare] = useState<{ url: string; copied: boolean; again: boolean } | null>(null);
  const onShare = () => {
    setNote("");
    void copyShareLink(plan.id).then(({ url, copied }) => setShare({ url, copied, again: false }));
  };
  const onCopyAgain = () => {
    void copyShareLink(plan.id).then(({ url, copied }) => setShare({ url, copied, again: copied }));
  };
  // Only one report section is open at a time; opening one closes the others and opens the drop-downs inside it.
  const [openSection, setOpenSection] = useState<string | null>(null);
  const sum: PlanSummary = plan.plan;
  const ctx: PlainContext = { dev, calcNames: sum.calculation_names ?? {}, flagText: sum.flag_text ?? {} };
  const calcNames = ctx.calcNames;

  const records = obj(sum.building.city_records);
  const prod = sum.solar.production;
  const o = sum.outcome;
  const budget = Number(plan.profile.budget_amount) || 0;
  const section = (id: string): Section | undefined => sum.sections.find((s) => s.section_id === id);
  // The data behind each report section: the records, prices, calculations and sources the written statements rest on.
  const data: Record<string, ReactNode> = {
    building: (
<Detail title="Your building" note="what you entered and what the city says">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">What you entered</p>
            <KV data={plan.profile as Obj} />
            <p className="pt-2 text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">City tax-lot and building-outline record</p>
            <KV data={records} skip={["ll84", "ll24", "differs_from_intake"]} />
            {Array.isArray(records.differs_from_intake) && (records.differs_from_intake as Obj[]).length > 0 && (
              <>
                <p className="pt-2 text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">Where the city record differs from what you entered</p>
                {(records.differs_from_intake as Obj[]).map((d) => (
                  <p key={String(d.field)} className="text-sm text-[var(--fr-ink)]">
                    {fieldLabel(String(d.field))}: you entered {fieldValue(String(d.field), d.intake)}; the city record says {fieldValue(String(d.field), d.city_record)}.
                  </p>
                ))}
              </>
            )}
            <p className="pt-2 text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">What the plan noticed about the site</p>
            <KV data={obj(sum.building.site_context)} />
          </Detail>
    ),
    energy: (
<Detail title="Energy use and your goal" note={sum.baseline.source}>
            <KV data={sum.baseline as unknown as Obj} />
            {sum.building.energy_report && (<><p className="pt-2 text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">City energy report (Local Law 84)</p><KV data={obj(sum.building.energy_report)} /></>)}
          </Detail>
    ),
    roof: (
<Detail title="The city's roof assessment" note="Local Law 24">
            {sum.building.roof_assessment ? <KV data={obj(sum.building.roof_assessment)} /> : <p className="text-sm text-[var(--fr-mute)]">This building is not in the city&rsquo;s roof assessment data.</p>}
          </Detail>
    ),
    solar: (
<Detail title="Solar" note="expected output and the roof math">
            {prod && <ToolMeta payload={prod as Obj} />}
            {prod && <KV data={obj((prod as Obj).data)} />}
            {Object.entries(sum.calculations).map(([id, calc]) => (
              <div key={id} className="rounded-lg border border-[var(--fr-line)] p-3">
                <div className="mb-1 text-sm font-semibold text-[var(--fr-ink)]">
                  {String(obj(calc).name ?? calcNames[id] ?? id)}
                  {dev && <span className="ml-1 font-mono text-[10px] text-[var(--fr-warn)]">{id}</span>}
                </div>
                <KV data={calc as Obj} skip={["label"]} />
              </div>
            ))}
          </Detail>
    ),
    price: (
<Detail title="Electricity price and rate schedules">
            {sum.prices.electricity && <><ToolMeta payload={sum.prices.electricity} /><KV data={obj(sum.prices.electricity.data)} /></>}
            {sum.prices.tariff && (
              <>
                <ToolMeta payload={sum.prices.tariff} />
                <KV data={obj(sum.prices.tariff.data)} skip={["candidate_tariffs"]} />
                {Array.isArray(obj(sum.prices.tariff.data).candidate_tariffs) && (
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    {(obj(sum.prices.tariff.data).candidate_tariffs as Obj[]).map((t) => (
                      <li key={String(t.tariff_name)}><SourceLink url={t.openei_url}>{String(t.tariff_name)}</SourceLink> · effective {String(t.effective_date)} · fixed charge ${show(t.fixed_charge_usd_per_month)} a month</li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </Detail>
    ),
    prices: (
<Detail title="Where the prices come from" note="solar, battery and efficiency">
            {(["solar", "battery", "efficiency"] as const).map((k) => {
              const b = obj(obj(sum.cost_basis)[k]);
              return (
                <div key={k} className="rounded-lg border border-[var(--fr-line)] p-3 text-sm">
                  <div className="font-semibold text-[var(--fr-ink)]">{k === "solar" ? "Solar panels" : k === "battery" ? "Backup battery" : "Efficiency work"}</div>
                  <p className="text-[var(--fr-mute)]">{b.basis ? <LinkedText text={dev ? String(b.basis) : plainify(String(b.basis))} /> : "Planning estimate, not yet based on project data."}</p>
                  {b.price != null && <p className="text-[var(--fr-ink)]">Price used: {priceText(k, b.price)}</p>}
                  <SourceLink url={b.source_url} />
                </div>
              );
            })}
            {obj(sum.cost_basis).efficiency_savings_realization != null && (
              <p className="text-sm text-[var(--fr-ink)]">Efficiency savings counted at {fieldValue("efficiency_savings_realization", obj(sum.cost_basis).efficiency_savings_realization)} of what was predicted, which is what the City&rsquo;s own audited projects delivered.</p>
            )}
            {typeof obj(sum.cost_basis).assumption_text === "string" && <p className="text-xs text-[var(--fr-mute)]"><LinkedText text={dev ? String(obj(sum.cost_basis).assumption_text) : plainify(String(obj(sum.cost_basis).assumption_text))} /></p>}
          </Detail>
    ),
    battery: (
<ToolBlock title="Backup battery size" payload={sum.battery} />
    ),
    hazards: (
<ToolBlock title="Flood zone" payload={sum.hazards} />
    ),
    assumptions: (
<Detail title="Assumptions behind the numbers" note={`${sum.assumptions.length} stated`}>
            <ul className="space-y-1.5 text-sm">
              {sum.assumptions.map((a) => (
                <li key={a.id}>{dev && <span className="mr-2 rounded bg-[var(--fr-soft)] px-1.5 py-0.5 font-mono text-xs text-[var(--fr-warn)]">{a.id}</span>}{dev ? a.text : plainify(a.text)}</li>
              ))}
            </ul>
          </Detail>
    ),
    tools: (
<Detail title="Where each number came from" note={`${sum.tools.length} sources`}>
            <table className="w-full text-left text-xs">
              <thead><tr className="text-[var(--fr-mute)]"><th className="py-1 pr-2">Source</th><th className="py-1 pr-2">Kind of data</th><th className="py-1 pr-2">Read on</th><th className="py-1 pr-2">Link</th></tr></thead>
              <tbody>
                {sum.tools.map((t) => (
                  <tr key={t.tool} className="border-t border-[var(--fr-line)] align-top">
                    <td className="py-1.5 pr-2 font-medium text-[var(--fr-ink)]">{toolLabel(t.tool)}{dev && <span className="ml-1 font-mono text-[10px] text-[var(--fr-warn)]">{t.tool}</span>}</td>
                    <td className="py-1.5 pr-2">{t.mock ? SAMPLE_BADGE_TEXT : "Live"}</td>
                    <td className="py-1.5 pr-2">{t.retrieved_at?.slice(0, 10) ?? ""}</td>
                    <td className="py-1.5 pr-2"><SourceLink url={t.source_url}>{dev && t.dataset_version ? t.dataset_version : "open"}</SourceLink></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Detail>
    ),
    links: (
<Detail title="Source links" note={`${sum.sources.length} pages`}>
            <ul className="space-y-1 text-sm">
              {sum.sources.map((s) => (
                <li key={s.url}><SourceLink url={s.url}>{s.label}</SourceLink>{s.retrieved_at ? <span className="text-xs text-[var(--fr-mute)]"> · read {s.retrieved_at.slice(0, 10)}</span> : null}{s.sample ? <span className="text-xs text-[#b7791f]"> · {SAMPLE_BADGE_TEXT}</span> : null}</li>
              ))}
            </ul>
          </Detail>
    ),
    usage: (
(dev && sum.usage && <Detail title="What this plan cost to make (developer view)"><KV data={obj(sum.usage)} /></Detail>)
    ),
  };
  // Side-by-side tables that open sections 6 and 7; the section's written statements stay below them, folded.
  const top: Record<string, ReactNode> = {};
  if (sum.scenarios.length > 0) {
    top["6"] = <ComparisonTable sum={sum} budget={budget} recommended={o.recommended} claims={section("6")?.claims ?? []} />;
    top["7"] = <CostTable sum={sum} recommended={o.recommended} claims={section("7")?.claims ?? []} />;
  }
  // Which data blocks sit under which report section (sections not listed have only their written statements).
  const SECTION_DATA: Record<string, string[]> = {
    "2": ["building"],
    "3": ["assumptions"],
    "4": ["energy"],
    "5": ["roof", "solar"],
    "6": ["price"],
    "7": ["prices"],
    "9": ["battery", "hazards"],
    "13": ["tools", "links", "usage"],
  };
  const toneBg = o.tone === "good" ? "linear-gradient(135deg,#dff3ea,#fdf0cf)" : o.tone === "caution" ? "linear-gradient(135deg,#fdf0cf,#faf6ee)" : "linear-gradient(135deg,#e3ecf6,#faf6ee)";
  const byId = (id: string) => sum.scenarios.find((s) => s.scenario_id === id);
  const allClaims = sum.sections.flatMap((s) => s.claims);
  const labelCounts = Object.fromEntries(Object.keys(LABELS).map((k) => [k, allClaims.filter((c) => c.label === k).length]));
  const total = allClaims.length || 1;
  const missingReason = o.code === "needs_roof_check" ? "Waiting on your roof check. Solar is not sized on a pitched roof from a guess." : "This option could not be costed for this building. See what to confirm first.";
  const phases = (section("8")?.claims ?? []).map((c) => {
    const m = (dev ? c.text : plainify(c.text)).match(/^Phase (\d)[,:]?\s*([^:]+):\s*(.*)$/i);
    return { claim: c, n: m?.[1] ?? "", title: m ? m[2].charAt(0).toUpperCase() + m[2].slice(1) : c.text, body: m ? m[3].charAt(0).toUpperCase() + m[3].slice(1) : "" };
  });

  return (
    <PlainCtx.Provider value={ctx}>
    <section className="mx-auto max-w-6xl space-y-10 px-4 py-8">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <button type="button" onClick={onRestart} className="text-[var(--fr-mute)] hover:text-[var(--fr-ink)]">← Home</button>
        <span className="text-[var(--fr-line)]">|</span>
        <span className="font-semibold text-[var(--fr-ink)]">{String(plan.profile.building_name ?? plan.label)}</span>
        <span className="rounded-full bg-[var(--fr-soft)] px-2 py-0.5 text-xs text-[var(--fr-mute)]">{plan.status === "done" ? "Plan complete" : "Plan complete, with open items"}</span>
        <div className="ml-auto flex items-center gap-2">
          <label className="flex cursor-pointer items-center gap-1.5 text-xs text-[var(--fr-mute)]">
            <input type="checkbox" checked={dev} onChange={(e) => setDev(e.target.checked)} />
            Developer view
          </label>
          {note && <span className="text-xs text-[var(--fr-mute)]" role="status">{note}</span>}
          <button type="button" onClick={onDownload} className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-[var(--fr-ink)] hover:border-[var(--fr-teal)]">Download PDF</button>
          <div className="relative">
            <button type="button" onClick={onShare} className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-[var(--fr-ink)] hover:border-[var(--fr-teal)]">Share</button>
            {share && (
              <div role="dialog" aria-label="Share this report" onKeyDown={(e) => { if (e.key === "Escape") setShare(null); }} className="absolute right-0 z-30 mt-2 w-80 rounded-xl border border-[var(--fr-line)] bg-white p-3 text-sm shadow-lg">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-[var(--fr-ink)]">{share.copied ? "\u2713 Link copied" : "Copy this link"}</span>
                  <button type="button" onClick={() => setShare(null)} aria-label="Close" className="px-1 text-[var(--fr-mute)] hover:text-[var(--fr-ink)]">&times;</button>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <input readOnly aria-label="Share link" value={shortLink(share.url)} title={share.url} onFocus={(e) => e.currentTarget.select()} className="min-w-0 flex-1 truncate rounded-lg border border-[var(--fr-line)] bg-[var(--fr-soft)] px-2.5 py-1.5 text-xs text-[var(--fr-ink)]" />
                  <button type="button" onClick={onCopyAgain} className="shrink-0 rounded-lg bg-[var(--fr-ink)] px-3 py-1.5 text-xs font-semibold text-white">{share.again ? "Copied" : "Copy link"}</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-3xl p-7 md:p-9" style={{ background: toneBg }}>
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--fr-teal)]">The short answer · {o.label}</div>
        <h1 className="mt-2 max-w-3xl text-3xl font-bold leading-tight text-[var(--fr-ink)] md:text-4xl">{o.headline}</h1>
        <p className="mt-3 max-w-3xl text-lg text-[var(--fr-ink)]/80">{o.subhead}</p>
        {sum.confirm_first.length > 0 && (
          <div className="mt-6 max-w-3xl rounded-2xl border border-[var(--fr-gold)] bg-white/80 p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-warn)]">Please confirm first</div>
            <ul className="mt-2 space-y-1.5 text-sm text-[var(--fr-ink)]/90">
              {sum.confirm_first.map((c) => (
                <li key={c.text} className="flex gap-2"><span className="text-[var(--fr-gold)]">●</span><span>{c.text}</span></li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <Card>
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--fr-teal)]">How to read this plan</div>
        <h2 className="mt-1 text-xl font-bold text-[var(--fr-ink)]">What to trust, what to check, and what to hand to a professional</h2>
        <p className="mt-2 text-sm text-[var(--fr-ink)]/80">Every number is labeled &ndash; {allClaims.length} statements in this plan</p>

        <div className="mt-4 flex h-3 overflow-hidden rounded-full bg-[var(--fr-soft)]">
          {Object.keys(LABELS).map((k) => (
            <div key={k} style={{ width: `${(labelCounts[k] / total) * 100}%`, background: LABELS[k].color }} title={`${k}: ${labelCounts[k]}`} />
          ))}
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Object.keys(LABELS).map((k) => {
            const e = LABEL_EXPLAINED[k];
            return (
              <div key={k} className="flex flex-col gap-2 rounded-xl bg-[var(--fr-soft)] p-3">
                <div className="flex items-baseline justify-between gap-2">
                  <Chip label={k} />
                  <span className="text-lg font-bold leading-none text-[var(--fr-ink)]">{labelCounts[k]}</span>
                </div>
                <p className="text-sm font-semibold text-[var(--fr-ink)]">{e.meaning}</p>
                <p className="text-xs text-[var(--fr-mute)]"><span className="font-semibold text-[var(--fr-ink)]">For example: </span>{e.example}</p>
                <p className="text-xs text-[var(--fr-mute)]"><span className="font-semibold text-[var(--fr-ink)]">What to do: </span>{e.action}</p>
              </div>
            );
          })}
        </div>

        <p className="mt-4 border-t border-[var(--fr-line)] pt-3 text-xs text-[var(--fr-mute)]">
          <span className="font-semibold text-[var(--fr-ink)]">Why costs and savings are ranges.</span> This is an early estimate made from public data, before anyone has walked the building. A range of about half to double the figure is normal at this stage. An energy audit and contractor bids are what narrow it.
        </p>
      </Card>

      <div>
        <SectionTitle eyebrow="Your options" title="Three ways to get there" sub="Each is an estimate shown as a range. The line on each bar is your goal or your budget." />
        <div className="grid gap-4 lg:grid-cols-3">
          {(["A", "B", "C"] as const).map((id) => (
            <ScenarioCard key={id} id={id} s={byId(id)} budget={budget} recommended={o.recommended === id} reason={missingReason} />
          ))}
        </div>
      </div>

      {(sum.not_included ?? []).length > 0 && (
          <Card className="border-[var(--fr-gold)] bg-[#fffaf0]">
            <div className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-warn)]">Not in these totals</div>
            {sum.not_included.map((n) => (
              <div key={n.item} className="mt-2 text-sm text-[var(--fr-ink)]">
                <div className="font-semibold">{n.item}{n.rough_guide_usd ? `: roughly ${moneyRange(n.rough_guide_usd)}` : ""}</div>
                <p className="text-[var(--fr-mute)]">{n.why} {n.next}</p>
                {n.basis && <p className="mt-1 text-xs text-[var(--fr-mute)]">{n.basis}</p>}
                {n.sources && n.sources.length > 0 && (
                  <ul className="mt-1 list-disc space-y-0.5 pl-5 text-xs text-[var(--fr-mute)]">
                    {n.sources.map((g) => (
                      <li key={g.url}>{g.label} <SourceLink url={g.url}>link</SourceLink></li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </Card>
        )}

      <div className="grid gap-8 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <SectionTitle eyebrow="Your roadmap" title="What to do, in order" />
          <ol className="space-y-3">
            {phases.map((ph) => (
              <li key={ph.claim.text} className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--fr-ink)] text-sm font-bold text-white">{ph.n || "•"}</div>
                <div className="flex-1 rounded-xl border border-[var(--fr-line)] bg-white p-3">
                  <div className="font-semibold text-[var(--fr-ink)]">{ph.title}</div>
                  {ph.body && <p className="text-sm text-[var(--fr-mute)]">{ph.body}</p>}
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-[var(--fr-mute)]">
                    <Chip label={ph.claim.label} />
                    {ph.claim.calc_id && <span>worked out from: {calcNames[ph.claim.calc_id] ?? ph.claim.calc_id}</span>}
                    <SourceLink url={ph.claim.source_url} />
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </div>
        <div>
          <SectionTitle eyebrow="Before you commit" title="Professionals you'll need" sub="Required reviews, not optional extras." />
          <Card>
            <ul className="space-y-2.5">
              {sum.referrals.map((r) => (
                <li key={r.text} className="flex gap-2 text-sm text-[var(--fr-ink)]">
                  <span className="mt-1 h-4 w-4 shrink-0 rounded border border-[var(--fr-mute)]" />
                  <span>{dev ? r.text : plainify(r.text)} <SourceLink url={r.source_url} /></span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      <div>
        <SectionTitle eyebrow="Money and rules" title="Incentives that may apply" sub="Each was re-read from its official page when this plan was made. A program that could not be confirmed is left out of the costs." />
        {sum.incentives.length > 0 ? (
          <div className="grid gap-3 md:grid-cols-2">{sum.incentives.map((p) => <ProgramCard key={p.name} p={p} />)}</div>
        ) : (
          <Card className="bg-[var(--fr-soft)]"><p className="text-sm text-[var(--fr-ink)]">No incentive information was returned for this plan. No incentive is counted in the costs.</p></Card>
        )}
      </div>

      {sum.next_steps.length > 0 && (
        <div>
          <SectionTitle eyebrow="Where to start" title="Who to contact" sub="Official pages, chosen for this building." />
          <div className="grid gap-3 md:grid-cols-2">
            {sum.next_steps.map((n) => (
              <Card key={n.url}>
                <a href={n.url} target="_blank" rel="noreferrer" className="font-semibold text-[var(--fr-teal)] underline">{n.name}</a>
                <p className="mt-1 text-sm text-[var(--fr-mute)]">{n.why}</p>
                {n.contact && <p className="mt-1 text-sm text-[var(--fr-ink)]">{n.contact}</p>}
              </Card>
            ))}
          </div>
        </div>
      )}

      <div>
        <SectionTitle eyebrow="The full report" title="Every statement and every record, section by section" sub="The complete written plan in the order of the 13 report sections. Under each section, the data behind it: the city records, prices, calculations and sources it rests on." />
        <div className="space-y-2">
          {sum.sections.map((s) => {
            const parts = (SECTION_DATA[s.section_id] ?? []).map((k) => ({ k, node: data[k] })).filter((x) => Boolean(x.node));
            return (
              <Detail
                key={s.section_id}
                open={openSection === s.section_id}
                onToggle={(e) => {
                  const el = e.currentTarget;
                  if (el.open && openSection !== s.section_id) {
                    setOpenSection(s.section_id);
                    // The sections above may have just closed, so bring this one to the top of the screen.
                    requestAnimationFrame(() => el.scrollIntoView({ behavior: "smooth", block: "start" }));
                  } else if (!el.open && openSection === s.section_id) {
                    setOpenSection(null);
                  }
                }}
                title={`${s.section_id}. ${SECTION_NAME[s.section_id] ?? s.title}`}
                note={`${s.claims.length} statements${parts.length ? ` · ${parts.length} data block${parts.length === 1 ? "" : "s"}` : ""}`}
              >
                <OpenCtx.Provider value={openSection === s.section_id}>
                {top[s.section_id] ? (
                  <div>{top[s.section_id]}</div>
                ) : s.claims.length === 0 ? (
                  <p className="text-sm text-[var(--fr-mute)]">Nothing was provided for this section.</p>
                ) : (
                  <ul className="grid gap-3 sm:grid-cols-2">{s.claims.map((c) => <ClaimRow key={c.text} claim={c} />)}</ul>
                )}
                {parts.length > 0 && (
                  <div className="mt-4 space-y-2 border-t border-[var(--fr-line)] pt-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-teal)]">The data behind this section</p>
                    {parts.map((x) => <div key={x.k}>{x.node}</div>)}
                  </div>
                )}
                </OpenCtx.Provider>
              </Detail>
            );
          })}
        </div>
      </div>

      <div className="rounded-3xl bg-[var(--fr-ink)] p-7 text-white">
        <h3 className="text-xl font-semibold">Try another building</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {plans.filter((p) => p.id !== plan.id).map((p) => (
            <button key={p.id} type="button" onClick={() => onPick(p.id)} className="rounded-full border border-white/30 px-3 py-1.5 text-sm hover:bg-white/10">{p.label.split(":")[0]}</button>
          ))}
        </div>
      </div>
      <p className="pb-6 text-center text-xs text-[var(--fr-mute)]">Planning-level estimates, not quotes. Every plan names the professionals who must review it before any money is committed.</p>
    </section>
    </PlainCtx.Provider>
  );
}
