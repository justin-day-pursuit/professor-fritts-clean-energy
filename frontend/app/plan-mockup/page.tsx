/**
 * /plan-mockup: the design page for the branded experience (home, guided intake, run narration, results).
 *
 * It is not wired to the live app. It reads ./data/plans.json, which holds real runs recorded from the backend (written by
 * `python manage.py export_plan_summaries`), and calls no API and no Claude, so the design can be edited while looking at a
 * real plan with no server and no cost. The existing pages (/, /planner) are unchanged; the "Developer tools" menu links to them.
 *
 * Deep links for review: /plan-mockup?view=results&sample=<case id>  (view: home | intake | running | results,
 * and step=1..4 for the intake).
 */
"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Results } from "./plan-view";
import { PLANS, type PlanView } from "./plans";
import { Card, Chip, LABELS, PALETTE, SectionTitle } from "./ui";

type View = "home" | "intake" | "running" | "results";

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

function narrationFor(sample: PlanView): string[] {
  const seen: string[] = [];
  for (const tool of sample.tools) {
    const line = NARRATION[tool];
    if (line && !seen.includes(line)) seen.push(line);
  }
  return [...seen, "Checking every number has a label and a source", "Writing your plan"];
}

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
            {PLANS.map((s) => (
              <button key={s.id} type="button" onClick={() => onPick(s.id)} className="rounded-2xl border border-[var(--fr-line)] bg-white p-5 text-left transition hover:-translate-y-0.5 hover:shadow-lg">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                    style={{
                      background: s.outcome.tone === "good" ? "#dff3ea" : s.outcome.tone === "caution" ? "#fdf0cf" : "#e3ecf6",
                      color: "#12303d",
                    }}
                  >
                    {s.outcome.label}
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

function Intake({ sample, step, setStep, onRun }: { sample: PlanView; step: number; setStep: (n: number) => void; onRun: () => void }) {
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

function Running({ sample, onDone }: { sample: PlanView; onDone: () => void }) {
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

// --------------------------------------------------------------------------------------------- page

export default function PlanMockup() {
  const [view, setView] = useState<View>("home");
  const [sampleId, setSampleId] = useState<string>(PLANS[0]?.id ?? "");
  const [step, setStep] = useState(1);
  const sample = PLANS.find((s) => s.id === sampleId) ?? PLANS[0];

  // Deep links for review: ?view=results&sample=<id>&step=<n>
  useEffect(() => {
    // Read after first paint (in a timer) so the server and browser render the same home page first.
    const timer = setTimeout(() => {
      const q = new URLSearchParams(window.location.search);
      const v = q.get("view") as View | null;
      const s = q.get("sample");
      if (s && PLANS.some((x) => x.id === s)) setSampleId(s);
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

  if (!sample) {
    return <p className="p-8">No saved plans found. Run the export command described at the top of this file.</p>;
  }
  return (
    <div style={PALETTE} className="min-h-screen bg-[var(--fr-cream)] text-[var(--fr-ink)]">
      <div className="bg-[var(--fr-ink)] px-4 py-1.5 text-center text-xs text-white/90">
        Design page. Real runs recorded from the backend; nothing here calls Claude or the backend.
      </div>
      <TopBar onHome={() => goTo("home")} onStart={() => pick(PLANS[0].id)} />
      {view === "home" && <Home onPick={pick} onStart={() => pick(PLANS[0].id)} />}
      {view === "intake" && <Intake sample={sample} step={step} setStep={setStep} onRun={() => goTo("running")} />}
      {view === "running" && <Running sample={sample} onDone={() => goTo("results")} />}
      {view === "results" && (
        <Results plan={sample} plans={PLANS} onRestart={() => goTo("home")} onPick={(id) => { setSampleId(id); goTo("results"); }} />
      )}
    </div>
  );
}
