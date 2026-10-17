/**
 * The results page of the /plan-mockup design: one saved real run, shown in full and in plain language.
 *
 * Order: the short answer, how to read the plan, what to confirm first, the three plans, the roadmap, the professionals to
 * call, incentives, who to contact, how sure we are, then "all the data we found" (every record, price, calculation and tool
 * result the run produced) and the full report with every labeled statement. Nothing the run found is left off the page, but
 * code-style names (field names, flag names, calculation ids, tool names) appear only in the "Developer view".
 */
"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import { SAMPLE_BADGE_TEXT } from "./copy";
import type { Claim, PlanSummary, Program, Scenario, Section } from "./plan-types";
import { fieldLabel, fieldValue, isInternalField, plainify, toolLabel } from "./plain";
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

function Detail({ title, note, children, open = false }: { title: string; note?: string; children: ReactNode; open?: boolean }) {
  return (
    <details open={open} className="rounded-xl border border-[var(--fr-line)] bg-white p-4">
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

/** One labeled statement from the report, with what it was worked out from and where it came from. */
function ClaimRow({ claim }: { claim: Claim }) {
  const { dev, calcNames } = useContext(PlainCtx);
  const range = claim.value_low != null && claim.value_high != null ? `${show(claim.value_low)}${claim.value_low !== claim.value_high ? ` to ${show(claim.value_high)}` : ""} ${claim.units ?? ""}` : "";
  return (
    <li className="flex flex-col gap-1 rounded-lg border border-[var(--fr-line)] bg-white p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Chip label={claim.label} />
        <span className="text-[11px] text-[var(--fr-mute)]">{claim.confidence} confidence</span>
        {claim.calc_id && <span className="rounded bg-[var(--fr-soft)] px-1.5 py-0.5 text-[11px]">worked out from: {calcNames[claim.calc_id] ?? claim.calc_id}</span>}
        {dev && claim.assumption_id && <span className="rounded bg-[var(--fr-soft)] px-1.5 py-0.5 font-mono text-[11px] text-[var(--fr-warn)]">{claim.assumption_id}</span>}
        {dev && claim.calc_id && <span className="font-mono text-[11px] text-[var(--fr-warn)]">{claim.calc_id}</span>}
        <span className="text-[11px]"><SourceLink url={claim.source_url} /></span>
      </div>
      <p className="text-[var(--fr-ink)]">{dev ? claim.text : plainify(claim.text)}</p>
      {range && <p className="text-xs text-[var(--fr-mute)]">{range.trim()}</p>}
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
        {over ? <p className="mt-1 text-xs font-medium text-[var(--fr-warn)]">{moneyRange(s.budget_gap_usd as [number, number])} more than your budget</p> : null}
        {s.incentives_counted_usd[1] > 0 && <p className="mt-1 text-xs text-[var(--fr-mute)]">After a {moneyRange(s.incentives_counted_usd)} federal credit: {moneyRange(s.net_cost_usd)}</p>}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--fr-line)] pt-3 text-sm">
        <div><dt className="text-xs text-[var(--fr-mute)]">Saves each year</dt><dd className="font-semibold text-[var(--fr-ink)]">{moneyRange(s.annual_savings_usd)}</dd></div>
        <div><dt className="text-xs text-[var(--fr-mute)]">Pays back in</dt><dd className="font-semibold text-[var(--fr-ink)]">{yearsRange(s.payback_years)}</dd></div>
        <div><dt className="text-xs text-[var(--fr-mute)]">Backup power</dt><dd className="font-semibold text-[var(--fr-ink)]">{hoursRange(s.outage_hours)}</dd></div>
        <div><dt className="text-xs text-[var(--fr-mute)]">Portion of your goal met</dt><dd className="font-semibold text-[var(--fr-ink)]">{pctRange(s.share_of_goal_pct)}</dd></div>
      </dl>
      {s.budget_note && <p className="mt-3 text-xs text-[var(--fr-mute)]">{s.budget_note}</p>}
      {s.surplus_solar_kwh[1] > 0 && <p className="mt-3 rounded-lg bg-[var(--fr-soft)] p-2 text-xs text-[var(--fr-mute)]">This roof could make more power than the building uses ({show(s.surplus_solar_kwh[0])} to {show(s.surplus_solar_kwh[1])} kWh extra). The extra isn&rsquo;t counted as savings.</p>}

      <details className="mt-3 rounded-lg border border-[var(--fr-line)] p-3">
        <summary className="cursor-pointer text-sm font-semibold text-[var(--fr-ink)]">Itemized bill</summary>
        <table className="mt-2 w-full text-left text-xs">
          <thead><tr className="text-[var(--fr-mute)]"><th className="py-1 pr-2">Item</th><th className="py-1 pr-2">Cost range</th></tr></thead>
          <tbody>
            {s.cost_items.map((c) => (
              <tr key={c.item} className="border-t border-[var(--fr-line)] align-top">
                <td className="py-1.5 pr-2"><div className="font-medium text-[var(--fr-ink)]">{c.item}</div><div className="text-[var(--fr-mute)]"><LinkedText text={dev ? c.basis : plainify(c.basis)} /></div></td>
                <td className="whitespace-nowrap py-1.5 pr-2 text-[var(--fr-ink)]">{moneyRangeExact(c.usd)}</td>
              </tr>
            ))}
            <tr className="border-t-2 border-[var(--fr-ink)] font-semibold"><td className="py-1.5 pr-2">Upfront total</td><td className="py-1.5 text-[var(--fr-ink)]">{moneyRangeExact(s.upfront_usd)}</td></tr>
            <tr className="font-semibold"><td className="py-1.5 pr-2">Net after incentives counted</td><td className="py-1.5 text-[var(--fr-ink)]">{moneyRangeExact(s.net_cost_usd)}</td></tr>
          </tbody>
        </table>
      </details>
    </Card>
  );
}

// ------------------------------------------------------------------------------------------------ incentives

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
  const sum: PlanSummary = plan.plan;
  const ctx: PlainContext = { dev, calcNames: sum.calculation_names ?? {}, flagText: sum.flag_text ?? {} };
  const calcNames = ctx.calcNames;
  const o = sum.outcome;
  const budget = Number(plan.profile.budget_amount) || 0;
  const toneBg = o.tone === "good" ? "linear-gradient(135deg,#dff3ea,#fdf0cf)" : o.tone === "caution" ? "linear-gradient(135deg,#fdf0cf,#faf6ee)" : "linear-gradient(135deg,#e3ecf6,#faf6ee)";
  const byId = (id: string) => sum.scenarios.find((s) => s.scenario_id === id);
  const section = (id: string): Section | undefined => sum.sections.find((s) => s.section_id === id);
  const allClaims = sum.sections.flatMap((s) => s.claims);
  const labelCounts = Object.fromEntries(Object.keys(LABELS).map((k) => [k, allClaims.filter((c) => c.label === k).length]));
  const total = allClaims.length || 1;
  const missingReason = o.code === "needs_roof_check" ? "Waiting on your roof check. We won't size solar on a pitched roof from a guess." : "This option could not be costed for this building. See what to confirm first.";
  const phases = (section("8")?.claims ?? []).map((c) => {
    const m = (dev ? c.text : plainify(c.text)).match(/^Phase (\d)[,:]?\s*([^:]+):\s*(.*)$/i);
    return { claim: c, n: m?.[1] ?? "", title: m ? m[2].charAt(0).toUpperCase() + m[2].slice(1) : c.text, body: m ? m[3].charAt(0).toUpperCase() + m[3].slice(1) : "" };
  });
  const records = obj(sum.building.city_records);
  const prod = sum.solar.production;

  return (
    <PlainCtx.Provider value={ctx}>
    <section className="mx-auto max-w-6xl space-y-10 px-4 py-8">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <button type="button" onClick={onRestart} className="text-[var(--fr-mute)] hover:text-[var(--fr-ink)]">← Home</button>
        <span className="text-[var(--fr-line)]">|</span>
        <span className="font-semibold text-[var(--fr-ink)]">{String(plan.profile.building_name ?? plan.label)}</span>
        <span className="rounded-full bg-[var(--fr-soft)] px-2 py-0.5 text-xs text-[var(--fr-mute)]">{plan.status === "done" ? "Plan complete" : "Plan complete, with open items"}</span>
        <span className="rounded-full bg-[var(--fr-soft)] px-2 py-0.5 text-xs text-[var(--fr-mute)]">{plan.kind === "recorded" ? "From a real run" : "Scripted demo"}</span>
        <div className="ml-auto flex items-center gap-2">
          <label className="flex cursor-pointer items-center gap-1.5 text-xs text-[var(--fr-mute)]">
            <input type="checkbox" checked={dev} onChange={(e) => setDev(e.target.checked)} />
            Developer view
          </label>
          <button type="button" disabled className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-[var(--fr-mute)] opacity-60">Download PDF</button>
          <button type="button" disabled className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-[var(--fr-mute)] opacity-60">Share</button>
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

      <Card className="bg-[var(--fr-soft)]">
        <div className="text-sm font-semibold text-[var(--fr-ink)]">How to read this plan</div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(LABELS).map(([k, l]) => (
            <div key={k} className="text-sm"><Chip label={k} /><p className="mt-1 text-xs text-[var(--fr-mute)]">{l.blurb}</p></div>
          ))}
        </div>
        <p className="mt-3 text-xs text-[var(--fr-mute)]">Costs and savings are shown as ranges because this is an early estimate made from public data, before anyone has walked the building. A range of about half to double the figure is normal at this stage. An energy audit and contractor bids are what narrow it.</p>
      </Card>

      <div>
        <SectionTitle eyebrow="Your options" title="Three ways to get there" sub="Each is an estimate shown as a range. The line on each bar is your goal or your budget." />
        <div className="grid gap-4 lg:grid-cols-3">
          {(["A", "B", "C"] as const).map((id) => (
            <ScenarioCard key={id} id={id} s={byId(id)} budget={budget} recommended={o.recommended === id} reason={missingReason} />
          ))}
        </div>
      </div>

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
        <SectionTitle eyebrow="Money and rules" title="Incentives that may apply" sub="Each was re-read from its official page when this plan was made. A program we could not confirm is left out of the costs." />
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
        <SectionTitle eyebrow="Confidence" title="How sure are we?" sub="Every statement in this plan carries one of four labels." />
        <Card>
          <div className="flex h-5 overflow-hidden rounded-full">
            {Object.keys(LABELS).map((k) => (
              <div key={k} style={{ width: `${(labelCounts[k] / total) * 100}%`, background: LABELS[k].color }} title={`${k}: ${labelCounts[k]}`} />
            ))}
          </div>
          <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(LABELS).map(([k, l]) => (
              <div key={k} className="text-sm"><Chip label={k} count={labelCounts[k]} /><p className="mt-1 text-xs text-[var(--fr-mute)]">{l.blurb}</p></div>
            ))}
          </div>
          <p className="mt-3 text-xs text-[var(--fr-mute)]">{allClaims.length} labeled statements in this plan. Nothing is unlabeled.</p>
        </Card>
      </div>

      <div>
        <SectionTitle eyebrow="For the curious" title="All the data we found" sub="Every record, price, calculation and source the plan rests on, exactly as the tools returned it." />
        <div className="space-y-2">
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
          <Detail title="Energy use and your goal" note={sum.baseline.source}>
            <KV data={sum.baseline as unknown as Obj} />
            {sum.building.energy_report && (<><p className="pt-2 text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">City energy report (Local Law 84)</p><KV data={obj(sum.building.energy_report)} /></>)}
          </Detail>
          <Detail title="The city's roof assessment" note="Local Law 24">
            {sum.building.roof_assessment ? <KV data={obj(sum.building.roof_assessment)} /> : <p className="text-sm text-[var(--fr-mute)]">This building is not in the city&rsquo;s roof assessment data.</p>}
          </Detail>
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
          <ToolBlock title="Backup battery size" payload={sum.battery} />
          <ToolBlock title="Flood zone" payload={sum.hazards} />
          <Detail title="Assumptions behind the numbers" note={`${sum.assumptions.length} stated`}>
            <ul className="space-y-1.5 text-sm">
              {sum.assumptions.map((a) => (
                <li key={a.id}>{dev && <span className="mr-2 rounded bg-[var(--fr-soft)] px-1.5 py-0.5 font-mono text-xs text-[var(--fr-warn)]">{a.id}</span>}{dev ? a.text : plainify(a.text)}</li>
              ))}
            </ul>
          </Detail>
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
          <Detail title="Source links" note={`${sum.sources.length} pages`}>
            <ul className="space-y-1 text-sm">
              {sum.sources.map((s) => (
                <li key={s.url}><SourceLink url={s.url}>{s.label}</SourceLink>{s.retrieved_at ? <span className="text-xs text-[var(--fr-mute)]"> · read {s.retrieved_at.slice(0, 10)}</span> : null}{s.sample ? <span className="text-xs text-[#b7791f]"> · {SAMPLE_BADGE_TEXT}</span> : null}</li>
              ))}
            </ul>
          </Detail>
          {dev && sum.usage && <Detail title="What this plan cost to make (developer view)"><KV data={obj(sum.usage)} /></Detail>}
        </div>
      </div>

      <div>
        <SectionTitle eyebrow="The full report" title="Every statement, section by section" sub="The complete written plan, in the order of the 13 report sections." />
        <div className="space-y-2">
          {sum.sections.map((s) => (
            <Detail key={s.section_id} title={`${s.section_id}. ${SECTION_NAME[s.section_id] ?? s.title}`} note={`${s.claims.length} statements`}>
              {s.claims.length === 0 ? <p className="text-sm text-[var(--fr-mute)]">Nothing was provided for this section.</p> : <ul className="space-y-2">{s.claims.map((c) => <ClaimRow key={c.text} claim={c} />)}</ul>}
            </Detail>
          ))}
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
