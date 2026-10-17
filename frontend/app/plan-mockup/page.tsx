/**
 * /plan-mockup: a THROWAWAY design mockup of the branded user experience (home, guided intake, run narration, results).
 *
 * It is not wired to the app. It reads only ./sample-data.ts (real numbers from our five saved runs) and calls no
 * API and no Claude, so it can be changed or deleted without touching anything else. The existing pages (/, /planner)
 * are unchanged; the "Developer tools" menu here just links to them, as the proposed site menu would.
 *
 * Deep links for review: /plan-mockup?view=results&sample=demo_ps236_bronx  (view: home | intake | running | results,
 * and step=1..4 for the intake).
 */
"use client";

import Image from "next/image";
import Link from "next/link";
import type { CSSProperties, ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { SAMPLES, type MockSample, type MockScenario, type Range } from "./sample-data";

type View = "home" | "intake" | "running" | "results";

/** Brand colors, taken from the logo. Scoped to this page only (globals.css is untouched). */
const PALETTE = {
  "--fr-cream": "#faf6ee",
  "--fr-soft": "#f1ecdf",
  "--fr-line": "#e6dfce",
  "--fr-ink": "#12303d",
  "--fr-mute": "#5b6b72",
  "--fr-teal": "#1c8c7e",
  "--fr-leaf": "#7bbf8a",
  "--fr-gold": "#f5b83d",
  "--fr-warn": "#c2562b",
} as CSSProperties;

/** The four labels every number carries: this is the product's signature. */
const LABELS: Record<string, { color: string; blurb: string }> = {
  FACT: { color: "#1c8c7e", blurb: "From a source we can name" },
  ESTIMATE: { color: "#2f6fb5", blurb: "Calculated, always shown as a range" },
  ASSUMPTION: { color: "#b7791f", blurb: "A stated starting point you can change" },
  RECOMMENDATION: { color: "#7a4fb0", blurb: "What we suggest you do" },
};

// ----------------------------------------------------------------------------------------------- helpers

function money(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2).replace(/0+$/, "").replace(/\.$/, "")}M`;
  return `$${Math.round(n / 1000).toLocaleString()}k`;
}
const moneyRange = (r: Range) => (r[0] === r[1] ? money(r[0]) : `${money(r[0])} to ${money(r[1])}`);
const pctRange = (r: Range) => (r[0] === r[1] ? `${r[0]}%` : `${r[0]}% to ${r[1]}%`);
const yearsRange = (r: Range | null) => (r ? `${Math.round(r[0])} to ${Math.round(r[1])} years` : "not available");
const hoursRange = (r: Range) => (r[1] <= 0 ? "None" : `${r[0]} to ${r[1]} hours`);

function Chip({ label, count }: { label: string; count?: number }) {
  const l = LABELS[label];
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold tracking-wide text-white"
      style={{ background: l?.color ?? "#555" }}
    >
      {label}
      {count != null ? <span className="opacity-80">· {count}</span> : null}
    </span>
  );
}

/** A horizontal bar showing a range on a 0..max scale, with an optional marker (the goal or the budget). */
function RangeBar({ low, high, max, color, marker, markerLabel }: { low: number; high: number; max: number; color: string; marker?: number; markerLabel?: string }) {
  const left = Math.min(100, (low / max) * 100);
  const width = Math.max(1.5, Math.min(100 - left, ((high - low) / max) * 100));
  return (
    <div className="relative pt-5">
      {marker != null && (
        <div
          className={`absolute top-0 whitespace-nowrap text-[10px] font-medium text-[var(--fr-mute)] ${(marker / max) > 0.8 ? "-translate-x-full pr-1" : "-translate-x-1/2"}`}
          style={{ left: `${Math.min(99, (marker / max) * 100)}%` }}
        >
          {markerLabel}
        </div>
      )}
      <div className="relative h-3 rounded-full bg-[var(--fr-soft)]">
        <div className="absolute top-0 h-3 rounded-full" style={{ left: `${left}%`, width: `${width}%`, background: color }} />
        {marker != null && <div className="absolute -top-1 h-5 w-px bg-[var(--fr-ink)]" style={{ left: `${Math.min(99, (marker / max) * 100)}%` }} />}
      </div>
    </div>
  );
}

function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-[var(--fr-line)] bg-white p-5 shadow-[0_1px_0_rgba(18,48,61,0.04)] ${className}`}>{children}</div>;
}

function SectionTitle({ eyebrow, title, sub }: { eyebrow?: string; title: string; sub?: string }) {
  return (
    <div className="mb-4">
      {eyebrow && <div className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--fr-teal)]">{eyebrow}</div>}
      <h2 className="text-2xl font-semibold text-[var(--fr-ink)]">{title}</h2>
      {sub && <p className="mt-1 max-w-2xl text-sm text-[var(--fr-mute)]">{sub}</p>}
    </div>
  );
}

/** Friendly narration for each tool the run used, in the order the run first used it. */
const NARRATION: Record<string, string> = {
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

function narrationFor(sample: MockSample): string[] {
  const seen: string[] = [];
  for (const tool of sample.tools) {
    const line = NARRATION[tool];
    if (line && !seen.includes(line)) seen.push(line);
  }
  return [...seen, "Checking every number has a label and a source", "Writing your plan"];
}

/** Plain-language lines for the data flags a plan raised; unknown flags are not shown. */
const FLAG_TEXT: Record<string, string> = {
  tariff_needs_user_confirmation: "Your electricity tariff is a saved sample. Confirm it against a recent bill.",
  stale_data: "Some saved data is older than our freshness rules allow.",
  mock_data_in_live_run: "Incentives, hazard ratings and battery sizing came from saved samples, not live data.",
  statewide_average_rate: "Savings use the New York average electricity price, not your own tariff.",
  "missing_field:roof_replaced_year": "We don't know when your roof was last replaced.",
  "missing_field:existing_systems": "You didn't tell us about systems the building already has.",
  "intake_mismatch:floor_area_sqft": "City records disagree with the floor area you entered.",
  address_street_mismatch: "The city lists a different street for this lot.",
  "tool_error:calculate": "We could not size solar for this roof yet.",
  "tool_error:get_solar_production": "We could not size a new solar array for this roof.",
};

// ------------------------------------------------------------------------------------------------ top bar

function TopBar({ onHome, onStart }: { onHome: () => void; onStart: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-20 border-b border-[var(--fr-line)] bg-[var(--fr-cream)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
        <button type="button" onClick={onHome} className="flex items-center gap-2 text-left">
          <Image src="/fritts-logo.png" alt="Professor Fritts" width={34} height={50} className="h-9 w-auto rounded-sm" />
          <span>
            <span className="block text-base font-bold leading-tight text-[var(--fr-ink)]">Professor Fritts</span>
            <span className="block text-[11px] uppercase tracking-[0.16em] text-[var(--fr-teal)]">Renewable energy planning</span>
          </span>
        </button>
        <nav className="ml-6 hidden items-center gap-5 text-sm text-[var(--fr-ink)] md:flex">
          <button type="button" onClick={onStart} className="hover:text-[var(--fr-teal)]">Plan a building</button>
          <a href="#samples" className="hover:text-[var(--fr-teal)]">Sample plans</a>
          <a href="#how" className="hover:text-[var(--fr-teal)]">How it works</a>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <span className="hidden rounded-full border border-dashed border-[var(--fr-warn)] px-2 py-0.5 text-[11px] font-medium text-[var(--fr-warn)] sm:inline">Design mockup</span>
          <div className="relative">
            <button type="button" onClick={() => setOpen((v) => !v)} className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-sm text-[var(--fr-ink)]">
              Developer tools ▾
            </button>
            {open && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl border border-[var(--fr-line)] bg-white p-1 text-sm shadow-lg">
                <Link href="/" className="block rounded-lg px-3 py-2 hover:bg-[var(--fr-soft)]">
                  Run sequences <span className="block text-xs text-[var(--fr-mute)]">The current home page</span>
                </Link>
                <Link href="/planner" className="block rounded-lg px-3 py-2 hover:bg-[var(--fr-soft)]">
                  Classic planner <span className="block text-xs text-[var(--fr-mute)]">Form, chat, run log, roadmap</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

// ------------------------------------------------------------------------------------------------- home

function Home({ onPick, onStart }: { onPick: (id: string) => void; onStart: () => void }) {
  return (
    <>
      <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-14 md:grid-cols-[1.25fr_1fr]">
        <div>
          <div className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--fr-teal)]">For NYC schools, libraries and public buildings</div>
          <h1 className="text-4xl font-bold leading-tight text-[var(--fr-ink)] md:text-5xl">
            Know what it takes to power your building with the sun, <span className="text-[var(--fr-teal)]">before you spend a dollar.</span>
          </h1>
          <p className="mt-4 max-w-xl text-lg text-[var(--fr-mute)]">
            Professor Fritts plans efficiency, solar and backup power for your building, then tells you exactly how sure it is about every number.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <button type="button" onClick={onStart} className="rounded-xl bg-[var(--fr-ink)] px-5 py-3 font-semibold text-white hover:opacity-90">
              Plan my building
            </button>
            <a href="#samples" className="rounded-xl border border-[var(--fr-ink)] px-5 py-3 font-semibold text-[var(--fr-ink)] hover:bg-white">
              See a sample plan
            </a>
          </div>
          <p className="mt-4 text-xs text-[var(--fr-mute)]">Named for Charles Fritts, who put the first solar panels on a New York City rooftop in 1884.</p>
        </div>
        <div className="mx-auto w-full max-w-xs rounded-3xl bg-white p-6 shadow-[0_20px_60px_rgba(18,48,61,0.12)]">
          <Image src="/fritts-logo.png" alt="Professor Fritts, renewable energy planning" width={368} height={540} className="h-auto w-full" priority />
        </div>
      </section>

      <section className="border-y border-[var(--fr-line)] bg-white">
        <div className="mx-auto max-w-6xl px-4 py-10">
          <SectionTitle eyebrow="What makes it different" title="Every number tells you how sure we are" sub="Most AI answers sound equally confident about everything. Ours labels each number, so you know what to trust, what to check, and what to hand to a professional." />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(LABELS).map(([name, l]) => (
              <div key={name} className="rounded-xl border border-[var(--fr-line)] p-4">
                <Chip label={name} />
                <p className="mt-2 text-sm text-[var(--fr-ink)]">{l.blurb}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="how" className="mx-auto max-w-6xl px-4 py-12">
        <SectionTitle eyebrow="How it works" title="From an address to a plan you can bring to your board" />
        <div className="grid gap-4 md:grid-cols-3">
          {[
            ["1", "Tell us about your building", "Start with the address. We pull what the city already knows, so you only fill in what it can't."],
            ["2", "Watch the Professor work", "He checks city records, estimates solar, looks up prices and rules, and costs three scenarios."],
            ["3", "Get a plan you can act on", "Three costed options, a step-by-step roadmap, and the professionals you'll need before any money is spent."],
          ].map(([n, t, d]) => (
            <Card key={n}>
              <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-[var(--fr-gold)] font-bold text-[var(--fr-ink)]">{n}</div>
              <h3 className="font-semibold text-[var(--fr-ink)]">{t}</h3>
              <p className="mt-1 text-sm text-[var(--fr-mute)]">{d}</p>
            </Card>
          ))}
        </div>
      </section>

      <section id="samples" className="bg-[var(--fr-soft)]">
        <div className="mx-auto max-w-6xl px-4 py-12">
          <SectionTitle eyebrow="Sample plans" title="See what you'd get" sub="Five real NYC buildings, planned from public data. Not every building gets a yes, and the plan says so honestly." />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {SAMPLES.map((s) => (
              <button key={s.id} type="button" onClick={() => onPick(s.id)} className="rounded-2xl border border-[var(--fr-line)] bg-white p-5 text-left transition hover:-translate-y-0.5 hover:shadow-lg">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                    style={{
                      background: s.copy.tone === "good" ? "#dff3ea" : s.copy.tone === "caution" ? "#fdf0cf" : "#e3ecf6",
                      color: "#12303d",
                    }}
                  >
                    {s.copy.outcome}
                  </span>
                  <span className="text-[11px] text-[var(--fr-mute)]">{s.kind === "recorded" ? "From a real run" : "Scripted demo"}</span>
                </div>
                <div className="font-semibold text-[var(--fr-ink)]">{s.label}</div>
                <p className="mt-1 text-sm text-[var(--fr-mute)]">{s.tag}</p>
                <div className="mt-3 text-sm font-medium text-[var(--fr-teal)]">Open this plan →</div>
              </button>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

// ----------------------------------------------------------------------------------------------- intake

const STEPS = ["Find your building", "Energy and goals", "What you already have", "Review and run"];

function Field({ label, value, hint }: { label: string; value: string | number | null | undefined; hint?: string }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-[var(--fr-ink)]">{label}</span>
      <input defaultValue={value ?? ""} key={String(value)} className="mt-1 w-full rounded-lg border border-[var(--fr-line)] bg-white px-3 py-2 text-[var(--fr-ink)] outline-none focus:border-[var(--fr-teal)]" />
      {hint && <span className="mt-1 block text-xs text-[var(--fr-mute)]">{hint}</span>}
    </label>
  );
}

function Found({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-2 text-sm text-[var(--fr-ink)]">
      <span className="mt-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--fr-teal)] text-[10px] text-white">✓</span>
      <span>{children}</span>
    </div>
  );
}

function Intake({ sample, step, setStep, onRun }: { sample: MockSample; step: number; setStep: (n: number) => void; onRun: () => void }) {
  const p = sample.profile;
  const pitched = String(p.roof_type ?? "").includes("pitch");
  return (
    <section className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-6 flex items-center gap-2">
        {STEPS.map((name, i) => (
          <div key={name} className="flex flex-1 items-center gap-2">
            <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${i + 1 <= step ? "bg-[var(--fr-teal)] text-white" : "bg-[var(--fr-soft)] text-[var(--fr-mute)]"}`}>{i + 1}</div>
            <span className={`hidden text-xs sm:block ${i + 1 === step ? "font-semibold text-[var(--fr-ink)]" : "text-[var(--fr-mute)]"}`}>{name}</span>
            {i < STEPS.length - 1 && <div className="h-px flex-1 bg-[var(--fr-line)]" />}
          </div>
        ))}
      </div>

      <Card>
        <div className="mb-1 text-xs font-semibold uppercase tracking-[0.14em] text-[var(--fr-teal)]">Step {step} of 4 · mockup pre-filled from a sample</div>
        <h2 className="mb-4 text-2xl font-semibold text-[var(--fr-ink)]">{STEPS[step - 1]}</h2>

        {step === 1 && (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-[2fr_1fr]">
              <Field label="Building address" value={p.address} />
              <Field label="Borough" value={p.borough} />
            </div>
            <div className="rounded-xl border border-[var(--fr-line)] bg-[var(--fr-soft)] p-4">
              <div className="mb-2 text-sm font-semibold text-[var(--fr-ink)]">We found your building in NYC records</div>
              <div className="grid gap-1.5 sm:grid-cols-2">
                <Found>{String(p.building_type).charAt(0).toUpperCase() + String(p.building_type).slice(1)} · built {p.year_built}</Found>
                <Found>{Number(p.floor_area_sqft).toLocaleString()} sq ft of floor area</Found>
                <Found>Roof suggestion: {Number(p.roof_area_sqft).toLocaleString()} sq ft, from city building footprints</Found>
                <Found>Served by {String(p.utility ?? "Con Edison")}</Found>
              </div>
              <p className="mt-3 text-xs text-[var(--fr-mute)]">A footprint isn&rsquo;t a measured roof. We&rsquo;ll ask you to have an engineer or roofer confirm it before any design.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Roof type" value={String(p.roof_type)} hint={pitched ? "A pitched roof needs a roofer's check before we size solar." : undefined} />
              <Field label="Roof area (sq ft)" value={p.roof_area_sqft} />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Electricity used per year (kWh)" value={p.annual_kwh} hint="Or upload 12 months of Con Edison bills." />
            <Field label="Capital budget" value={`$${Number(p.budget_amount).toLocaleString()}`} hint={`${p.budget_year} · capital`} />
            <div className="sm:col-span-2"><Field label="Your goal" value={String(p.goal)} /></div>
            <div className="sm:col-span-2"><Field label="Anything that must keep running in an outage?" value={p.critical_loads ?? ""} /></div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <p className="text-sm text-[var(--fr-mute)]">Tell us what the building already has, so the plan builds on it. Write &ldquo;none&rdquo; if there&rsquo;s nothing to list.</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Solar already on the roof (kW)" value={p.existing_solar_kw ?? "0"} />
              <Field label="Other renewables" value={p.existing_renewables ?? "none"} />
              <div className="sm:col-span-2"><Field label="Efficiency work already done" value={p.existing_efficiency ?? "none"} /></div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-3">
            <p className="text-sm text-[var(--fr-mute)]">Here&rsquo;s the question we&rsquo;ll answer:</p>
            <blockquote className="rounded-xl border-l-4 border-[var(--fr-gold)] bg-[var(--fr-soft)] p-4 text-[var(--fr-ink)]">&ldquo;{sample.question}&rdquo;</blockquote>
            <div className="grid gap-1.5 text-sm text-[var(--fr-ink)] sm:grid-cols-2">
              <Found>{String(p.building_name)}</Found>
              <Found>${Number(p.budget_amount).toLocaleString()} capital budget</Found>
              <Found>{Number(p.annual_kwh).toLocaleString()} kWh a year</Found>
              <Found>{String(p.goal)}</Found>
            </div>
          </div>
        )}

        <div className="mt-6 flex items-center justify-between">
          <button type="button" disabled={step === 1} onClick={() => setStep(step - 1)} className="rounded-lg px-3 py-2 text-sm text-[var(--fr-ink)] disabled:opacity-30">← Back</button>
          {step < 4 ? (
            <button type="button" onClick={() => setStep(step + 1)} className="rounded-xl bg-[var(--fr-ink)] px-5 py-2.5 font-semibold text-white">Continue</button>
          ) : (
            <button type="button" onClick={onRun} className="rounded-xl bg-[var(--fr-teal)] px-5 py-2.5 font-semibold text-white">Run Professor Fritts</button>
          )}
        </div>
      </Card>
    </section>
  );
}

// --------------------------------------------------------------------------------------------- running

function Running({ sample, onDone }: { sample: MockSample; onDone: () => void }) {
  const lines = useMemo(() => narrationFor(sample), [sample]);
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (shown >= lines.length) {
      const t = setTimeout(onDone, 900);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setShown((n) => n + 1), 750);
    return () => clearTimeout(t);
  }, [shown, lines.length, onDone]);
  const pct = Math.round((Math.min(shown, lines.length) / lines.length) * 100);
  return (
    <section className="mx-auto max-w-2xl px-4 py-14">
      <div className="mb-6 flex items-center gap-4">
        <Image src="/fritts-logo.png" alt="" width={56} height={82} className="h-16 w-auto rounded-md" />
        <div>
          <h2 className="text-2xl font-semibold text-[var(--fr-ink)]">The Professor is working on {String(sample.profile.building_name)}</h2>
          <p className="text-sm text-[var(--fr-mute)]">A live run takes about two minutes. This mockup plays it faster.</p>
        </div>
      </div>
      <div className="mb-5 h-2 overflow-hidden rounded-full bg-[var(--fr-soft)]">
        <div className="h-2 rounded-full bg-[var(--fr-teal)] transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <Card>
        <ul className="space-y-3">
          {lines.map((line, i) => {
            const done = i < shown;
            const active = i === shown;
            if (i > shown) return null;
            return (
              <li key={line} className="flex items-center gap-3 text-[var(--fr-ink)]">
                <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] ${done ? "bg-[var(--fr-teal)] text-white" : "border-2 border-[var(--fr-gold)]"} ${active ? "animate-pulse" : ""}`}>{done ? "✓" : ""}</span>
                <span className={done ? "text-[var(--fr-mute)]" : "font-medium"}>{line}{active ? "…" : ""}</span>
              </li>
            );
          })}
        </ul>
      </Card>
      <div className="mt-4 text-center">
        <button type="button" onClick={onDone} className="text-sm text-[var(--fr-mute)] underline">Skip to my plan</button>
      </div>
    </section>
  );
}

// --------------------------------------------------------------------------------------------- results

const SCENARIO_NAME: Record<string, string> = { A: "Efficiency only", B: "Efficiency + solar", C: "Full path + backup power" };

function ScenarioCard({ id, s, budget, recommended, sample }: { id: "A" | "B" | "C"; s?: MockScenario; budget: number; recommended: boolean; sample: MockSample }) {
  if (!s) {
    const reason = sample.id === "real1_jefferson_market_library" ? "Waiting on your roof check. We won't size solar on a pitched roof from a guess." : "There's no free roof space for a new solar array, so this option isn't available.";
    return (
      <Card className="border-dashed bg-[var(--fr-soft)]">
        <div className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">Plan {id}</div>
        <div className="text-lg font-semibold text-[var(--fr-ink)]">{SCENARIO_NAME[id]}</div>
        <p className="mt-3 text-sm text-[var(--fr-mute)]">Not costed yet.</p>
        <p className="mt-1 text-sm text-[var(--fr-ink)]">{reason}</p>
      </Card>
    );
  }
  const over = s.budget_strain === "over budget" && s.budget_gap_usd;
  const costMax = Math.max(s.upfront_usd[1], budget) * 1.08;
  const cutColor = s.reaches_goal ? "#1c8c7e" : "#b7791f";
  const costColor = over ? "#c2562b" : "#2f6fb5";
  return (
    <Card className={recommended ? "ring-2 ring-[var(--fr-gold)]" : ""}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-mute)]">Plan {id}</div>
          <div className="text-lg font-semibold text-[var(--fr-ink)]">{SCENARIO_NAME[id]}</div>
        </div>
        {recommended ? (
          <span className="rounded-full bg-[var(--fr-gold)] px-2.5 py-1 text-[11px] font-bold text-[var(--fr-ink)]">Recommended</span>
        ) : over ? (
          <span className="rounded-full bg-[#fbe3d9] px-2.5 py-1 text-[11px] font-bold text-[var(--fr-warn)]">Over budget</span>
        ) : (
          <span className="rounded-full bg-[#dff3ea] px-2.5 py-1 text-[11px] font-bold text-[var(--fr-ink)]">Fits budget</span>
        )}
      </div>

      <div className="mt-4">
        <div className="flex items-baseline justify-between text-sm"><span className="text-[var(--fr-mute)]">Cuts grid electricity</span><span className="font-semibold text-[var(--fr-ink)]">{pctRange(s.reduction_pct_of_use)}</span></div>
        <RangeBar low={s.reduction_pct_of_use[0]} high={s.reduction_pct_of_use[1]} max={100} color={cutColor} marker={30} markerLabel="30% goal" />
        <p className="mt-1 text-xs text-[var(--fr-mute)]">{s.reaches_goal ? "Reaches your goal even at the low end." : "Doesn't reach 30% at the low end."}</p>
      </div>

      <div className="mt-4">
        <div className="flex items-baseline justify-between text-sm"><span className="text-[var(--fr-mute)]">Upfront cost</span><span className="font-semibold text-[var(--fr-ink)]">{moneyRange(s.upfront_usd)}</span></div>
        <RangeBar low={s.upfront_usd[0]} high={s.upfront_usd[1]} max={costMax} color={costColor} marker={budget} markerLabel={`Budget ${money(budget)}`} />
        {over ? (
          <p className="mt-1 text-xs font-medium text-[var(--fr-warn)]">{moneyRange(s.budget_gap_usd as Range)} more than your budget</p>
        ) : null}
        {s.incentives_counted_usd[1] > 0 && <p className="mt-1 text-xs text-[var(--fr-mute)]">After a {moneyRange(s.incentives_counted_usd)} federal credit: {moneyRange(s.net_cost_usd)}</p>}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-[var(--fr-line)] pt-3 text-sm">
        <div><dt className="text-xs text-[var(--fr-mute)]">Pays back in</dt><dd className="font-semibold text-[var(--fr-ink)]">{yearsRange(s.payback_years)}</dd></div>
        <div><dt className="text-xs text-[var(--fr-mute)]">Backup power</dt><dd className="font-semibold text-[var(--fr-ink)]">{hoursRange(s.outage_hours)}</dd></div>
      </dl>
      {s.surplus_solar_kwh[1] > 0 && <p className="mt-3 rounded-lg bg-[var(--fr-soft)] p-2 text-xs text-[var(--fr-mute)]">This roof could make more power than the building uses. The extra isn&rsquo;t counted as savings.</p>}
    </Card>
  );
}

function Results({ sample, onRestart, onPick }: { sample: MockSample; onRestart: () => void; onPick: (id: string) => void }) {
  const c = sample.copy;
  const budget = Number(sample.profile.budget_amount);
  const toneBg = c.tone === "good" ? "linear-gradient(135deg,#dff3ea,#fdf0cf)" : c.tone === "caution" ? "linear-gradient(135deg,#fdf0cf,#faf6ee)" : "linear-gradient(135deg,#e3ecf6,#faf6ee)";
  const phases = sample.phases.map((t) => {
    const m = t.match(/^Phase (\d)[,:]?\s*([^:]+):\s*(.*)$/);
    return m ? { n: m[1], title: m[2].charAt(0).toUpperCase() + m[2].slice(1), body: m[3].charAt(0).toUpperCase() + m[3].slice(1) } : { n: "", title: t, body: "" };
  });
  const flagLines = sample.flags.map((f) => FLAG_TEXT[f]).filter(Boolean) as string[];
  const total = sample.claimTotal;
  return (
    <section className="mx-auto max-w-6xl space-y-10 px-4 py-8">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <button type="button" onClick={onRestart} className="text-[var(--fr-mute)] hover:text-[var(--fr-ink)]">← Home</button>
        <span className="text-[var(--fr-line)]">|</span>
        <span className="font-semibold text-[var(--fr-ink)]">{String(sample.profile.building_name)}</span>
        <span className="rounded-full bg-[var(--fr-soft)] px-2 py-0.5 text-xs text-[var(--fr-mute)]">{sample.status === "done" ? "Plan complete" : "Plan complete, with a next step"}</span>
        <span className="rounded-full bg-[var(--fr-soft)] px-2 py-0.5 text-xs text-[var(--fr-mute)]">{sample.kind === "recorded" ? "From a real run" : "Scripted demo"}</span>
        <div className="ml-auto flex gap-2">
          <button type="button" disabled className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-[var(--fr-mute)] opacity-60">Download PDF</button>
          <button type="button" disabled className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-[var(--fr-mute)] opacity-60">Share</button>
        </div>
      </div>

      <div className="rounded-3xl p-7 md:p-9" style={{ background: toneBg }}>
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--fr-teal)]">The short answer</div>
        <h1 className="mt-2 max-w-3xl text-3xl font-bold leading-tight text-[var(--fr-ink)] md:text-4xl">{c.headline}</h1>
        <p className="mt-3 max-w-3xl text-lg text-[var(--fr-ink)]/80">{c.subhead}</p>
        <div className="mt-6 max-w-3xl rounded-2xl border border-[var(--fr-gold)] bg-white/80 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-[var(--fr-warn)]">Your next step</div>
          <div className="mt-1 font-semibold text-[var(--fr-ink)]">{c.next.title}</div>
          <p className="mt-1 text-sm text-[var(--fr-ink)]/80">{c.next.body}</p>
        </div>
      </div>

      <div>
        <SectionTitle eyebrow="Your options" title="Three ways to get there" sub="Each is an estimate shown as a range. The line on each bar is your goal or your budget." />
        <div className="grid gap-4 lg:grid-cols-3">
          {(["A", "B", "C"] as const).map((id) => (
            <ScenarioCard key={id} id={id} s={sample.scenarios[id]} budget={budget} recommended={c.recommended === id} sample={sample} />
          ))}
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <SectionTitle eyebrow="Your roadmap" title="What to do, in order" />
          <ol className="space-y-3">
            {phases.map((ph) => (
              <li key={ph.n + ph.title} className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--fr-ink)] text-sm font-bold text-white">{ph.n}</div>
                <div className="rounded-xl border border-[var(--fr-line)] bg-white p-3">
                  <div className="font-semibold text-[var(--fr-ink)]">{ph.title}</div>
                  {ph.body && <p className="text-sm text-[var(--fr-mute)]">{ph.body}</p>}
                </div>
              </li>
            ))}
          </ol>
        </div>
        <div>
          <SectionTitle eyebrow="Before you commit" title="Professionals you'll need" sub="Required reviews, not optional extras." />
          <Card>
            <ul className="space-y-2.5">
              {sample.referrals.slice(0, 7).map((r) => (
                <li key={r} className="flex gap-2 text-sm text-[var(--fr-ink)]">
                  <span className="mt-1 h-4 w-4 shrink-0 rounded border border-[var(--fr-mute)]" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      <div>
        <SectionTitle eyebrow="Money and rules" title="Incentives that may apply" />
        {c.incentives ? (
          <div className="grid gap-3 md:grid-cols-2">
            {c.incentives.map((i) => (
              <Card key={i.name}>
                <div className="mb-1 flex items-center gap-2">
                  <span className="rounded-full px-2 py-0.5 text-[11px] font-bold text-white" style={{ background: i.status === "open" ? "#1c8c7e" : i.status === "uncertain" ? "#b7791f" : "#12303d" }}>
                    {i.status === "open" ? "Open" : i.status === "uncertain" ? "Not confirmed" : "Rule"}
                  </span>
                  <span className="text-xs text-[var(--fr-mute)]">Read from official pages on Oct 16, 2026</span>
                </div>
                <div className="font-semibold text-[var(--fr-ink)]">{i.name}</div>
                <p className="mt-1 text-sm text-[var(--fr-mute)]">{i.note}</p>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="bg-[var(--fr-soft)]">
            <span className="rounded-full bg-[#b7791f] px-2 py-0.5 text-[11px] font-bold text-white">Sample data</span>
            <p className="mt-2 text-sm text-[var(--fr-ink)]">Incentive information in this sample plan is saved sample data, not verified against official pages. No incentive is counted in the costs. The P.S. 236 plan shows what verified incentives look like.</p>
          </Card>
        )}
      </div>

      <div>
        <SectionTitle eyebrow="Confidence" title="How sure are we?" sub="Every one of the numbers and statements in this plan carries one of four labels." />
        <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
          <Card>
            <div className="flex h-5 overflow-hidden rounded-full">
              {Object.keys(LABELS).map((k) => (
                <div key={k} style={{ width: `${((sample.labelCounts[k] ?? 0) / total) * 100}%`, background: LABELS[k].color }} title={`${k}: ${sample.labelCounts[k] ?? 0}`} />
              ))}
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {Object.entries(LABELS).map(([k, l]) => (
                <div key={k} className="text-sm">
                  <Chip label={k} count={sample.labelCounts[k] ?? 0} />
                  <p className="mt-1 text-xs text-[var(--fr-mute)]">{l.blurb}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-[var(--fr-mute)]">{total} labeled statements in this plan. Nothing is unlabeled.</p>
          </Card>
          <Card className="bg-[var(--fr-soft)]">
            <div className="mb-2 font-semibold text-[var(--fr-ink)]">Worth knowing about this plan</div>
            <ul className="space-y-2 text-sm text-[var(--fr-ink)]">
              {flagLines.map((t) => (
                <li key={t} className="flex gap-2"><span className="text-[var(--fr-gold)]">●</span><span>{t}</span></li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      <div>
        <SectionTitle eyebrow="For the curious" title="See the details" />
        <div className="space-y-2">
          {([["Assumptions behind the numbers", sample.assumptions], ["What would make this plan more certain", sample.gaps], ["Sources", sample.sources]] as const).map(([title, items]) => (
            <details key={title} className="rounded-xl border border-[var(--fr-line)] bg-white p-4">
              <summary className="cursor-pointer font-semibold text-[var(--fr-ink)]">{title}</summary>
              <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-[var(--fr-mute)]">
                {items.map((t) => <li key={t}>{t}</li>)}
              </ul>
            </details>
          ))}
        </div>
      </div>

      <div className="rounded-3xl bg-[var(--fr-ink)] p-7 text-white">
        <h3 className="text-xl font-semibold">Try another building</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {SAMPLES.filter((s) => s.id !== sample.id).map((s) => (
            <button key={s.id} type="button" onClick={() => onPick(s.id)} className="rounded-full border border-white/30 px-3 py-1.5 text-sm hover:bg-white/10">{s.label.split(":")[0]}</button>
          ))}
        </div>
      </div>
      <p className="pb-6 text-center text-xs text-[var(--fr-mute)]">Planning-level estimates, not quotes. Every plan names the professionals who must review it before any money is committed.</p>
    </section>
  );
}

// --------------------------------------------------------------------------------------------- page

export default function PlanMockup() {
  const [view, setView] = useState<View>("home");
  const [sampleId, setSampleId] = useState<string>(SAMPLES[0].id);
  const [step, setStep] = useState(1);
  const sample = SAMPLES.find((s) => s.id === sampleId) ?? SAMPLES[0];

  // Deep links for review: ?view=results&sample=<id>&step=<n>
  useEffect(() => {
    // Read after first paint (in a timer) so the server and browser render the same home page first.
    const timer = setTimeout(() => {
      const q = new URLSearchParams(window.location.search);
      const v = q.get("view") as View | null;
      const s = q.get("sample");
      if (s && SAMPLES.some((x) => x.id === s)) setSampleId(s);
      if (v && ["home", "intake", "running", "results"].includes(v)) setView(v);
      const st = Number(q.get("step"));
      if (st >= 1 && st <= 4) setStep(st);
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  const goTo = (v: View) => {
    setView(v);
    if (typeof window !== "undefined") window.scrollTo({ top: 0 });
  };
  const pick = (id: string) => {
    setSampleId(id);
    setStep(1);
    goTo("intake");
  };

  return (
    <div style={PALETTE} className="min-h-screen bg-[var(--fr-cream)] text-[var(--fr-ink)]">
      <div className="bg-[var(--fr-ink)] px-4 py-1.5 text-center text-xs text-white/90">
        Design mockup. Sample data from our saved runs; nothing on this page calls Claude or the backend.
      </div>
      <TopBar onHome={() => goTo("home")} onStart={() => pick(SAMPLES[0].id)} />
      {view === "home" && <Home onPick={pick} onStart={() => pick(SAMPLES[0].id)} />}
      {view === "intake" && <Intake sample={sample} step={step} setStep={setStep} onRun={() => goTo("running")} />}
      {view === "running" && <Running sample={sample} onDone={() => goTo("results")} />}
      {view === "results" && <Results sample={sample} onRestart={() => goTo("home")} onPick={(id) => { setSampleId(id); goTo("results"); }} />}
    </div>
  );
}
