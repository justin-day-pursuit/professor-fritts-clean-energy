/**
 * The home page (/): the branded Professor Fritts experience (home, guided intake, real analysis, results).
 *
 * The saved sample plans come from ./data/plans.json, real runs recorded from the backend (written by
 * `python manage.py export_plan_summaries`); they replay with no server and no cost. A typed address starts a real analysis
 * through the backend (see ./live-run.ts). The older pages are kept: /dev/run-sequences (the run list) and /planner (the classic
 * planner); the "Developer tools" menu links to them.
 *
 * Deep links for review: /?view=results&sample=<case id>  (view: home | welcome | intake | running | ready | results,
 * and step=1..4 for the intake).
 *
 * Professor Fritts stays on screen through the whole visit (see ./fritts/). He greets in the middle, steps to the side during
 * the form, stands beside the work while it runs, announces the report in the middle, then steps to the side again. His lines
 * are scripted (./fritts/script.ts), so the guide uses no API and no credits.
 */
"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { AddressSearch } from "./AddressSearch";
import { buildingTypeLabel, fetchBuildingRecord, numberOf, ownerKind, type AddressSuggestion, type BuildingRecord, type FoundBuilding } from "./address";
import { FrittsGuide, type GuideAction } from "./fritts/FrittsGuide";
import { poseForStep, type Placement, type PoseName } from "./fritts/poses";
import { planRun } from "./fritts/runPlan";
import { getBuildingPrefill } from "@/lib/api";
import { LiveRunError, buildProfile, buildQuestion, missingForRun, narrationFor as narrationForTools, planFromRun, runLive, stepsSoFar, type RunForm } from "./live-run";
import type { BuildingPrefill, PrefillItem, RunResponse } from "@/lib/types";
import { ADDRESS_ERROR, ADDRESS_LOOKING, ADDRESS_NOT_FOUND, ADDRESS_START, BRING, BRING_REPLY, CONFIRM_REPLY, HELLO, INTAKE_STEP, PDF_SAYS, PREFILL_STEP, PRIVATE_BUILDING, REPORT_MENU, SHARE_LIVE, foundLine, readyLine, shareLine, unclearOwner, workingLine } from "./fritts/script";
import { plainify } from "./plain";
import { copyShareLink, downloadPlanPdf } from "./plan-actions";
import { Results } from "./plan-view";
import { PLANS, type PlanView } from "./plans";
import { Card, Chip, LABELS, PALETTE, SectionTitle } from "./ui";

/** How long Fritts shows "Let me look that up" before he reads the building back, so the step is seen even when the city answers at once. */
const LOOKING_MOMENT_MS = 1400;

type View = "welcome" | "home" | "intake" | "running" | "ready" | "results";

/** The sentences for the steps of a saved plan, from the tools its run used. */
function narrationFor(sample: PlanView): string[] {
  return narrationForTools(sample.tools);
}

// ------------------------------------------------------------------------------------------------ top bar

function TopBar({ onHome, onStart }: { onHome: () => void; onStart: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-20 border-b border-[var(--fr-line)] bg-[var(--fr-cream)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
        <button type="button" onClick={onHome} className="flex items-center gap-2 text-left">
          <Image src="/fritts-logo-mark.png" alt="Professor Fritts" width={525} height={575} className="h-9 w-auto rounded-sm" />
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
          <div className="relative">
            <button type="button" onClick={() => setOpen((v) => !v)} className="rounded-lg border border-[var(--fr-line)] bg-white px-3 py-1.5 text-sm text-[var(--fr-ink)]">
              Developer tools ▾
            </button>
            {open && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl border border-[var(--fr-line)] bg-white p-1 text-sm shadow-lg">
                <Link href="/dev/run-sequences" className="block rounded-lg px-3 py-2 hover:bg-[var(--fr-soft)]">
                  Run sequences <span className="block text-xs text-[var(--fr-mute)]">Test situations, live or scripted</span>
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
          <Image src="/fritts-logo.png" alt="Professor Fritts, renewable energy planning" width={465} height={735} className="h-auto w-full" priority />
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

function Field({ label, value, hint, onChange, readOnly }: { label: string; value: string | number | null | undefined; hint?: string; onChange?: (value: string) => void; readOnly?: boolean }) {
  const box = "mt-1 w-full rounded-lg border border-[var(--fr-line)] bg-white px-3 py-2 text-[var(--fr-ink)] outline-none focus:border-[var(--fr-teal)]";
  return (
    <label className="block">
      <span className="text-sm font-medium text-[var(--fr-ink)]">{label}</span>
      {onChange ? (
        // Typed into: the page keeps what was typed, so it can be sent to the planner.
        <input value={value ?? ""} onChange={(e) => onChange(e.target.value)} className={box} />
      ) : (
        <input defaultValue={value ?? ""} key={String(value)} readOnly={readOnly} className={box} />
      )}
      {hint && <span className="mt-1 block text-xs text-[var(--fr-mute)]">{hint}</span>}
    </label>
  );
}

/** The values the city's records suggested for the form, found by name, with a sentence saying where each came from. */
function prefillOf(prefill: BuildingPrefill | null, field: string): PrefillItem | undefined {
  return prefill?.items.find((item) => item.field === field);
}

/** The number or text to show in a box (the yes/no solar-ready answer is shown as a sentence instead, so it has no box value). */
function prefillValue(prefill: BuildingPrefill | null, field: string): string | number | undefined {
  const value = prefillOf(prefill, field)?.value;
  return typeof value === "boolean" ? undefined : value;
}

/** What the city's records suggest for the boxes the visitor can type in, as text. */
function suggestedFrom(prefill: BuildingPrefill | null): RunForm {
  const text = (field: string) => {
    const value = prefillValue(prefill, field);
    return value === undefined ? undefined : String(value);
  };
  return { annual_kwh: text("annual_kwh"), roof_area_sqft: text("roof_area_sqft"), existing_solar_kw: text("existing_solar_kw") };
}

/** The small print under a pre-filled box: where the value came from and what to keep in mind. */
function prefillHint(item: PrefillItem | undefined, fallback?: string): string | undefined {
  return item ? `From ${item.source}. ${item.note}` : fallback;
}

/** A drop-down box, for a choice with a few set answers. */
function SelectField({ label, value, options, hint, onChange }: { label: string; value: string | undefined; options: [string, string][]; hint?: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-[var(--fr-ink)]">{label}</span>
      <select value={value ?? ""} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded-lg border border-[var(--fr-line)] bg-white px-3 py-2 text-[var(--fr-ink)] outline-none focus:border-[var(--fr-teal)]">
        {options.map(([v, text]) => (
          <option key={v} value={v}>
            {text}
          </option>
        ))}
      </select>
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

/**
 * A place to attach a recent electric bill. For a building the visitor typed in, the file goes to the planner with the run:
 * a CSV with month and kWh columns is read for the yearly electricity use, and other files are kept but not read yet.
 * When the form is filled in from a saved sample, the file is only named on screen.
 */
function BillUpload({ onFile, forRun }: { onFile: (file: File | null) => void; forRun: boolean }) {
  const [name, setName] = useState("");
  const attached = forRun
    ? `Attached: ${name}. A CSV with month and kWh columns is read for your yearly use; any other file is kept with your plan but not read yet.`
    : `Attached: ${name}. This replay does not read it, so the plan still uses the city's energy report.`;
  return (
    <div className="rounded-xl border-2 border-dashed border-[var(--fr-line)] bg-[var(--fr-soft)] p-4 sm:col-span-2">
      <label htmlFor="bill-upload" className="block text-sm font-medium text-[var(--fr-ink)]">Attach a recent electric bill (optional)</label>
      <input
        id="bill-upload"
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.csv"
        onChange={(e) => {
          const file = e.target.files?.[0] ?? null;
          setName(file?.name ?? "");
          onFile(file);
        }}
        className="mt-2 block w-full text-sm text-[var(--fr-mute)] file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--fr-ink)] file:px-3 file:py-1.5 file:text-white"
      />
      <p className="mt-2 text-xs text-[var(--fr-mute)]">{name ? attached : "A bill lets the plan use your real electricity price and yearly use."}</p>
    </div>
  );
}

/** A dollar amount for a form box, or nothing when there is no amount yet. */
function dollars(value: string | number | null | undefined): string {
  return value ? `$${Number(value).toLocaleString()}` : "";
}

/** What the visitor has chosen so far on the first step, and how to change it. */
interface IntakeProps {
  /** The saved sample plan. It fills the form in "sample" mode and is what Run replays in both modes. */
  sample: PlanView;
  /** "search": the visitor looks up their own address. "sample": the form is pre-filled from a saved sample. */
  mode: "search" | "sample";
  found: FoundBuilding | null;
  /** What the city's free records suggest for this building, or null while it is loading, was not reachable, or no address is chosen. */
  prefill: BuildingPrefill | null;
  /** What is in each box for a typed address: the city's suggestion until the visitor types over it. */
  values: RunForm;
  onChange: (name: keyof RunForm, value: string) => void;
  /** What is still missing when the visitor pressed Run, or null. */
  runProblem: string | null;
  /** The electric bill the visitor attached, or null. */
  onBill: (file: File | null) => void;
  /** Changes when the address box should be emptied and started again. */
  searchKey: number;
  searchValue: string;
  onPickAddress: (choice: AddressSuggestion) => void;
  onEditAddress: () => void;
  onSearched: (text: string, count: number) => void;
  onPickSample: (id: string) => void;
  step: number;
  setStep: (n: number) => void;
  onRun: () => void;
}

function Intake({ sample, mode, found, prefill, values, onChange, runProblem, onBill, searchKey, searchValue, onPickAddress, onEditAddress, onSearched, onPickSample, step, setStep, onRun }: IntakeProps) {
  const searching = mode === "search";
  const rec = found?.record ?? null;
  // In search mode the form starts with only what the city's records say; in sample mode it is filled from the sample.
  const p: Record<string, string | number | null | undefined> = searching
    ? { address: found?.label, borough: found?.borough }
    : sample.profile;
  const pitched = String(p.roof_type ?? "").includes("pitch");
  const canContinue = step > 1 || !searching || (found !== null && (found.kind === "public" || found.accepted));
  return (
    <div className="px-4 pb-56 lg:pb-0 lg:pr-[28rem] xl:pr-4 xl:pl-[calc(max(1rem,(100vw-1344px)/2)+40px)]">
    <section className="mx-auto max-w-3xl py-10 xl:mx-0">
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
        <div className="mb-1 text-xs font-semibold uppercase tracking-[0.14em] text-[var(--fr-teal)]">Step {step} of 4{searching ? "" : " · filled in from a sample"}</div>
        <h2 className="mb-4 text-2xl font-semibold text-[var(--fr-ink)]">{STEPS[step - 1]}</h2>

        {step === 1 && searching && (
          <div className="space-y-4">
            <AddressSearch key={searchKey} value={searchValue} onPick={onPickAddress} onEdit={onEditAddress} onSearched={onSearched} />
            {found && (
              <div className="rounded-xl border border-[var(--fr-line)] bg-[var(--fr-soft)] p-4">
                <div className="mb-2 text-sm font-semibold text-[var(--fr-ink)]">{found.record ? "We found your building in NYC records" : "We found the address, but the city has no record for this lot"}</div>
                {found.record && (
                  <div className="grid gap-1.5 sm:grid-cols-2">
                    <Found>{buildingTypeLabel(found.record)}{numberOf(found.record.yearbuilt) ? ` · built ${found.record.yearbuilt}` : ""}</Found>
                    {numberOf(found.record.bldgarea) && <Found>{Number(found.record.bldgarea).toLocaleString()} sq ft of floor area</Found>}
                    {numberOf(found.record.numfloors) && <Found>{Math.round(Number(found.record.numfloors))} floors</Found>}
                    {found.record.ownername && <Found>Owner on the city record: {found.record.ownername}</Found>}
                  </div>
                )}
                <p className="mt-3 text-xs text-[var(--fr-mute)]">The roof comes next. A roof size from city records isn&rsquo;t a measured roof, so we&rsquo;ll ask you to have an engineer or roofer confirm it before any design.</p>
                {found.kind !== "public" && !found.accepted && (
                  <p className="mt-2 text-xs font-medium text-[var(--fr-warn)]">
                    {found.kind === "private" ? "This looks like a private building. This planner is made for New York City's public buildings." : "The owner on the city record doesn't make clear whether this is a public building."}
                  </p>
                )}
              </div>
            )}
            <div className="rounded-3xl bg-[var(--fr-ink)] p-5 text-white">
              <h3 className="text-base font-semibold">Or try a sample building</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {PLANS.map((s) => (
                  <button key={s.id} type="button" onClick={() => onPickSample(s.id)} className="rounded-full border border-white/30 px-3 py-1.5 text-sm hover:bg-white/10">
                    {s.label.split(":")[0]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 1 && !searching && (
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
            <div className="text-xs text-[var(--fr-mute)]">
              <button type="button" onClick={() => onPickSample("")} className="underline hover:text-[var(--fr-teal)]">Search for your own address instead</button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="grid gap-3 sm:grid-cols-2">
            <Field
              label="Electricity used per year (kWh)"
              value={searching ? values.annual_kwh : p.annual_kwh}
              onChange={searching ? (v) => onChange("annual_kwh", v) : undefined}
              hint={prefillHint(prefillOf(prefill, "annual_kwh"), "Or attach a recent bill below.")}
            />
            <Field label="Capital budget" value={searching ? values.budget_amount : dollars(p.budget_amount)} onChange={searching ? (v) => onChange("budget_amount", v) : undefined} hint={searching ? "The most you could spend on the work, for example $400,000." : `${p.budget_year} · capital`} />
            <div className="sm:col-span-2"><Field label="Your goal" value={searching ? values.goal : p.goal == null ? "" : String(p.goal)} onChange={searching ? (v) => onChange("goal", v) : undefined} hint={searching ? "For example: cut grid electricity 30% by 2030." : undefined} /></div>
            <div className="sm:col-span-2"><Field label="Anything that must keep running in an outage?" value={searching ? values.critical_loads : (p.critical_loads ?? "")} onChange={searching ? (v) => onChange("critical_loads", v) : undefined} /></div>
            <BillUpload onFile={onBill} forRun={searching} />
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <p className="text-sm text-[var(--fr-mute)]">Tell us what the building already has, so the plan builds on it. Write &ldquo;none&rdquo; if there&rsquo;s nothing to list.</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {searching && (
                <>
                  <Field label="Roof area (sq ft)" value={values.roof_area_sqft} onChange={(v) => onChange("roof_area_sqft", v)} hint={prefillHint(prefillOf(prefill, "roof_area_sqft"), "Not sure? An engineer or roofer can measure the usable area.")} />
                  <SelectField
                    label="Roof type"
                    value={values.roof_type}
                    onChange={(v) => onChange("roof_type", v)}
                    options={[["", "Choose…"], ["flat", "Flat"], ["pitched", "Pitched (sloped)"], ["mixed", "Mixed, towers or domes"]]}
                    hint="A pitched or mixed roof needs an engineer or roofer before solar is sized."
                  />
                  <Field
                    label="Roof condition (the city's assessment)"
                    value={prefillOf(prefill, "roof_condition")?.display}
                    readOnly
                    hint={prefillHint(prefillOf(prefill, "roof_condition"), "The city has no roof assessment for this building.")}
                  />
                  {prefillOf(prefill, "solar_ready") && (
                    <div className="sm:col-span-2">
                      <Found>{prefillOf(prefill, "solar_ready")?.display}</Found>
                    </div>
                  )}
                </>
              )}
              <Field
                label="Solar already on the roof (kW)"
                value={searching ? (values.existing_solar_kw ?? "") : (p.existing_solar_kw ?? "0")}
                onChange={searching ? (v) => onChange("existing_solar_kw", v) : undefined}
                hint={prefillHint(prefillOf(prefill, "existing_solar_kw"))}
              />
              <Field label="Other renewables" value={searching ? values.existing_renewables : (p.existing_renewables ?? "none")} onChange={searching ? (v) => onChange("existing_renewables", v) : undefined} />
              <div className="sm:col-span-2"><Field label="Efficiency work already done" value={searching ? values.existing_efficiency : (p.existing_efficiency ?? "none")} onChange={searching ? (v) => onChange("existing_efficiency", v) : undefined} /></div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-3">
            {searching ? (
              <>
                <p className="text-sm text-[var(--fr-mute)]">Here&rsquo;s the building I&rsquo;ll plan for:</p>
                <div className="grid gap-1.5 text-sm text-[var(--fr-ink)] sm:grid-cols-2">
                  <Found>{found?.label ?? "No address chosen yet"}</Found>
                  {rec && <Found>{buildingTypeLabel(rec)}</Found>}
                </div>
                <p className="rounded-xl bg-[var(--fr-soft)] p-3 text-xs text-[var(--fr-mute)]">
                  Pressing Run starts a real analysis of this building. It takes about two minutes, and it uses your answers and the city&rsquo;s public records.
                </p>
                {runProblem && <p className="rounded-xl border border-[var(--fr-gold)] bg-white p-3 text-sm text-[var(--fr-ink)]">{runProblem}</p>}
              </>
            ) : (
              <>
                <p className="text-sm text-[var(--fr-mute)]">Here&rsquo;s the question we&rsquo;ll answer:</p>
                <blockquote className="rounded-xl border-l-4 border-[var(--fr-gold)] bg-[var(--fr-soft)] p-4 text-[var(--fr-ink)]">&ldquo;{sample.question}&rdquo;</blockquote>
                <div className="grid gap-1.5 text-sm text-[var(--fr-ink)] sm:grid-cols-2">
                  <Found>{String(p.building_name)}</Found>
                  <Found>${Number(p.budget_amount).toLocaleString()} capital budget</Found>
                  <Found>{Number(p.annual_kwh).toLocaleString()} kWh a year</Found>
                  <Found>{String(p.goal)}</Found>
                </div>
              </>
            )}
          </div>
        )}

        <div className="mt-6 flex items-center justify-between">
          <button type="button" disabled={step === 1} onClick={() => setStep(step - 1)} className="rounded-lg px-3 py-2 text-sm text-[var(--fr-ink)] disabled:opacity-30">← Back</button>
          {step < 4 ? (
            <button type="button" disabled={!canContinue} onClick={() => setStep(step + 1)} className="rounded-xl bg-[var(--fr-ink)] px-5 py-2.5 font-semibold text-white disabled:opacity-40">Continue</button>
          ) : (
            <button type="button" onClick={onRun} className="rounded-xl bg-[var(--fr-teal)] px-5 py-2.5 font-semibold text-white">Run Professor Fritts</button>
          )}
        </div>
      </Card>
    </section>
    </div>
  );
}

// --------------------------------------------------------------------------------------------- running

/**
 * The working list. The page owns the progress so Fritts can say each step out loud as it appears. A saved plan plays its
 * steps on a timer. A real run shows the steps the agent has actually taken, so the bar can only estimate how far along it is.
 */
function Running({ name, lines, shown, live, error, onDone, onBack }: { name: string; lines: string[]; shown: number; live: boolean; error: string | null; onDone: () => void; onBack: () => void }) {
  // A real run does not know its length ahead of time: the bar fills toward about a dozen steps and stays short of full until the plan is ready.
  const pct = live ? Math.min(95, Math.round(((shown + 1) / 12) * 100)) : Math.round((Math.min(shown, lines.length) / lines.length) * 100);
  return (
    <section className="mx-auto max-w-5xl px-4 py-14 pb-56 lg:pb-14 lg:pl-[24rem]">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-[var(--fr-ink)]">The Professor is working on {name}</h2>
        <p className="text-sm text-[var(--fr-mute)]">
          {live ? "A real analysis takes about two minutes. Please keep this page open." : "A live run takes about two minutes. This replay plays it faster."}
        </p>
      </div>
      {error ? (
        <Card>
          <p className="text-[var(--fr-ink)]">{error}</p>
          <button type="button" onClick={onBack} className="mt-4 rounded-xl bg-[var(--fr-ink)] px-5 py-2.5 font-semibold text-white">Back to my answers</button>
        </Card>
      ) : (
        <>
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
          {!live && (
            <div className="mt-4 text-center">
              <button type="button" onClick={onDone} className="text-sm text-[var(--fr-mute)] underline">Skip to my plan</button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

// --------------------------------------------------------------------------------------------- page

/** The plain screen behind Fritts while he is in the middle: the greeting and the "your report is ready" moment. */
function Backdrop({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <section className="relative flex min-h-[calc(100vh-6.5rem)] flex-col items-center px-4 pt-12 text-center" style={{ background: "radial-gradient(ellipse at 50% 100%, #d9efe9 0%, transparent 62%)" }}>
      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--fr-teal)]">{eyebrow}</div>
      <h1 className="mt-2 max-w-5xl text-3xl font-bold leading-tight text-[var(--fr-ink)] md:whitespace-nowrap md:text-[clamp(1.25rem,2.8vw,2.25rem)]">{title}</h1>
    </section>
  );
}

/** The first sentence of a statement, used when Fritts reads a section aloud. */
function firstSentence(text: string): string {
  return text.split(/(?<=[.!?])\s+(?=[A-Z$(])/)[0];
}

/** What Fritts says, where he stands and which buttons he offers, for the screen the visitor is on. */
interface GuideState {
  placement: Placement;
  pose: PoseName;
  line: string;
  actions: GuideAction[];
  /** A wider bubble for a long list of buttons. */
  wide?: boolean;
}

export default function PlanMockup() {
  const [view, setView] = useState<View>("home");
  const [sampleId, setSampleId] = useState<string>(PLANS[0]?.id ?? "");
  const [step, setStep] = useState(1);
  // What the city's free records suggest for each lot the visitor has picked, kept by lot number; "failed" means the backend did not answer.
  const [prefills, setPrefills] = useState<Record<string, BuildingPrefill | "failed">>({});
  // What the visitor typed over the city's suggestions, by box. A box shows the suggestion until something is typed.
  const [typed, setTyped] = useState<RunForm>({});
  // "sample" replays a saved plan; "live" is a real run for the visitor's own address.
  const [runMode, setRunMode] = useState<"sample" | "live">("sample");
  // A real run in progress (the steps it has taken so far), or the reason it did not give a plan.
  const [live, setLive] = useState<{ status: "idle" | "running" | "error"; run: RunResponse | null; message: string }>({ status: "idle", run: null, message: "" });
  // The plan a real run produced. The report screen shows it in place of a saved sample.
  const [livePlan, setLivePlan] = useState<PlanView | null>(null);
  // What was still missing when Run was pressed.
  const [runProblem, setRunProblem] = useState<string | null>(null);
  // The electric bill attached on the energy step, sent to the planner with a real run.
  const [bill, setBill] = useState<File | null>(null);
  // Counts up each time a real run starts or the visitor leaves the run, so a run they walked away from cannot pull them back.
  const liveToken = useRef(0);
  const sample = livePlan ?? PLANS.find((s) => s.id === sampleId) ?? PLANS[0];

  // What Fritts is in the middle of: the greeting, the answers he has been given, the working list and the report menu.
  const [cue, setCue] = useState(0);
  const [welcomePhase, setWelcomePhase] = useState<"hello" | "bring">("hello");
  const [bringChoice, setBringChoice] = useState<keyof typeof BRING_REPLY | null>(null);
  const [confirm, setConfirm] = useState<keyof typeof CONFIRM_REPLY | null>(null);
  // The first step of the form: the visitor's own address search, or a pre-filled sample.
  const [mode, setMode] = useState<"search" | "sample">("search");
  const [chosen, setChosen] = useState<AddressSuggestion | null>(null);
  const [records, setRecords] = useState<Record<string, BuildingRecord | null>>({});
  const [failedBbl, setFailedBbl] = useState<string | null>(null);
  // The lot whose "looking it up" moment has been on screen long enough, so a fast answer does not flash past.
  const [lookShown, setLookShown] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [searchStatus, setSearchStatus] = useState<"idle" | "empty" | "error">("idle");
  const [searchValue, setSearchValue] = useState("");
  const [searchKey, setSearchKey] = useState(0);
  const [runShown, setRunShown] = useState(0);
  const [menu, setMenu] = useState<"menu" | "sections" | "said">("menu");
  const [said, setSaid] = useState("");
  // The share link Fritts last copied, so his menu can offer "Copy link" again.
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  // What the city's records say about the chosen address, worked out from the state above so a slow answer for an
  // address the visitor has since changed can never show up.
  const hasRecord = chosen !== null && chosen.bbl in records && lookShown === chosen.bbl;
  const found: FoundBuilding | null =
    chosen && hasRecord
      ? { label: chosen.label, borough: chosen.borough, bbl: chosen.bbl, record: records[chosen.bbl], kind: ownerKind(records[chosen.bbl]), accepted }
      : null;
  // The records for the lot chosen now (never an earlier choice's), or null while loading or when the backend did not answer.
  const chosenPrefill = chosen && prefills[chosen.bbl] !== "failed" ? (prefills[chosen.bbl] as BuildingPrefill | undefined) ?? null : null;
  const lookup: "idle" | "looking" | "empty" | "error" =
    chosen && !hasRecord ? (failedBbl === chosen.bbl ? "error" : "looking") : searchStatus;
  // The steps in the order of Fritts's scenes, with when each one starts (see ./fritts/runPlan.ts).
  const savedRunPlan = useMemo(() => planRun(sample ? narrationFor(sample) : []), [sample]);
  // A real run shows the steps the agent has actually taken so far; a saved plan plays its steps on a timer.
  const liveSteps = useMemo(() => stepsSoFar(live.run?.events ?? []), [live.run]);
  const runLines = runMode === "live" ? liveSteps : savedRunPlan.lines;
  // How many steps are finished: for a real run, all but the last one, which is being worked on now.
  const shownNow = runMode === "live" ? liveSteps.length - 1 : runShown;
  // What is in each box for a typed address: the city's suggestion, until the visitor types over it.
  const values: RunForm = { ...suggestedFrom(chosenPrefill), ...typed };

  /** Moves to a screen, scrolls to the top, and resets whatever Fritts should start fresh on that screen. */
  const goTo = useCallback((v: View) => {
    setView(v);
    // Leaving for the home page, the welcome or the form stops following a real run that is still going.
    if (v === "home" || v === "welcome" || v === "intake") liveToken.current += 1;
    if (typeof window !== "undefined") window.scrollTo({ top: 0 });
    if (v === "welcome" || v === "ready") setCue((c) => c + 1);
    if (v === "welcome") {
      setWelcomePhase("hello");
      setBringChoice(null);
    }
    if (v === "running") setRunShown(0);
    if (v === "results") {
      setMenu("menu");
      setSaid("");
      setShareUrl(null);
    }
  }, []);

  // Deep links for review: ?view=results&sample=<id>&step=<n>
  useEffect(() => {
    // Read after first paint (in a timer) so the server and browser render the same home page first.
    const timer = setTimeout(() => {
      const q = new URLSearchParams(window.location.search);
      const v = q.get("view") as View | null;
      const s = q.get("sample");
      if (s && PLANS.some((x) => x.id === s)) setSampleId(s);
      if (v && ["home", "welcome", "intake", "running", "ready", "results"].includes(v)) goTo(v);
      const st = Number(q.get("step"));
      if (st >= 1 && st <= 4) setStep(st);
    }, 0);
    return () => clearTimeout(timer);
  }, [goTo]);

  // The working list plays itself, each step lasting as long as its part of Fritts's scene, then the report is ready.
  useEffect(() => {
    if (view !== "running" || runMode !== "sample") return;
    if (runShown >= runLines.length) {
      const t = setTimeout(() => goTo("ready"), 900);
      return () => clearTimeout(t);
    }
    // Each step lasts until the next one starts, so every scene of Fritts plays one full pass of its animation.
    const stepEnd = savedRunPlan.starts[runShown + 1] ?? savedRunPlan.total;
    const t = setTimeout(() => setRunShown((n) => n + 1), stepEnd - savedRunPlan.starts[runShown]);
    return () => clearTimeout(t);
  }, [view, runMode, runShown, runLines.length, savedRunPlan, goTo]);

  /** Starts a real analysis for the building the visitor chose and follows it to the end. */
  const startLiveRun = async (building: FoundBuilding) => {
    const question = buildQuestion(values);
    const mine = ++liveToken.current;
    setRunMode("live");
    setLivePlan(null);
    setLive({ status: "running", run: null, message: "" });
    goTo("running");
    try {
      const run = await runLive(buildProfile(building, values), question, (latest) => setLive((prev) => ({ ...prev, run: latest })), {
        isCancelled: () => liveToken.current !== mine,
        bill,
      });
      if (liveToken.current !== mine) return;
      const plan = planFromRun(run, question);
      if (!plan) throw new LiveRunError("failed", "The analysis finished without a plan. Please try again.");
      setLivePlan(plan);
      setLive({ status: "idle", run: null, message: "" });
      goTo("ready");
    } catch (error) {
      if (liveToken.current !== mine) return;
      const failure = error instanceof LiveRunError ? error : new LiveRunError("failed", "Something went wrong. Please try again.");
      setLive({ status: "error", run: null, message: failure.message });
    }
  };
  /** Run: a typed address starts a real analysis; a saved sample replays its saved plan. */
  const onRun = () => {
    setRunProblem(null);
    if (mode === "search" && found) {
      const missing = missingForRun(found, values);
      if (missing.length > 0) {
        setRunProblem(`Before I can start I still need your ${missing.join(" and ")}.`);
        return;
      }
      void startLiveRun(found);
      return;
    }
    setRunMode("sample");
    goTo("running");
  };

  /** Forgets any building chosen and empties the address box. */
  const resetSearch = () => {
    setTyped({});
    setRunProblem(null);
    setChosen(null);
    setAccepted(false);
    setSearchStatus("idle");
    setSearchValue("");
    setConfirm(null);
    setSearchKey((k) => k + 1);
  };
  /** The "Plan my building" buttons: Fritts greets first, then the form with an empty address box. */
  const startExperience = () => {
    setLivePlan(null);
    setSampleId(PLANS[0].id);
    setStep(1);
    setMode("search");
    resetSearch();
    goTo("welcome");
  };
  /** A sample card on the home page: straight to the form, filled in from that sample. */
  const pick = (id: string) => {
    setLivePlan(null);
    setSampleId(id);
    setStep(1);
    setMode("sample");
    setConfirm(null);
    goTo("intake");
  };
  /** A sample chosen on the form's first step (or, with no id, a return to searching). */
  const pickSample = (id: string) => {
    setStep(1);
    setConfirm(null);
    if (!id) {
      setMode("search");
      resetSearch();
      return;
    }
    setLivePlan(null);
    setSampleId(id);
    setMode("sample");
  };
  /** The visitor picked an address from the list: read the city's tax-lot record, which says who owns the lot. */
  const pickAddress = (choice: AddressSuggestion) => {
    setTyped({});
    setRunProblem(null);
    setSearchValue(choice.label);
    setChosen(choice);
    setAccepted(false);
    setConfirm(null);
    setFailedBbl(null);
    setLookShown(null);
    setTimeout(() => setLookShown(choice.bbl), LOOKING_MOMENT_MS);
    if (choice.bbl in records) return;
    fetchBuildingRecord(choice.bbl)
      .then((record) => setRecords((prev) => ({ ...prev, [choice.bbl]: record })))
      .catch(() => setFailedBbl(choice.bbl));
    // Ask the backend for the free city records that fill the energy and roof questions (no Claude). If it is not
    // reachable the form simply stays blank, as before.
    if (!(choice.bbl in prefills)) {
      getBuildingPrefill(choice.bbl, choice.label, choice.borough)
        .then((result) => setPrefills((prev) => ({ ...prev, [choice.bbl]: result })))
        .catch(() => setPrefills((prev) => ({ ...prev, [choice.bbl]: "failed" })));
    }
  };
  /** The visitor typed again, so the earlier choice no longer stands. */
  const editAddress = () => {
    setChosen(null);
    setAccepted(false);
    setConfirm(null);
  };
  /** A search finished. Nothing found for a real-looking address means it is not in New York City; -1 means the service failed. */
  const searched = (text: string, count: number) => {
    setSearchStatus(count < 0 ? "error" : count === 0 && text.length >= 4 ? "empty" : "idle");
  };

  if (!sample) {
    return <p className="p-8">No saved plans found. Run the export command described at the top of this file.</p>;
  }

  // ---- Fritts: where he stands, what he says and which buttons he offers on each screen.
  const guide = ((): GuideState | null => {
    if (view === "welcome") {
      if (welcomePhase === "hello") {
        return { placement: "center", pose: "welcome", line: HELLO, actions: [{ label: "Let's begin", primary: true, onClick: () => setWelcomePhase("bring") }] };
      }
      if (!bringChoice) {
        return {
          placement: "center",
          pose: "explaining",
          line: BRING,
          actions: [
            { label: "I have everything", onClick: () => setBringChoice("all") },
            { label: "I have some of it", onClick: () => setBringChoice("some") },
            { label: "Not sure yet", onClick: () => setBringChoice("unsure") },
          ],
        };
      }
      return {
        placement: "center",
        pose: bringChoice === "unsure" ? "reassuring" : "delighted",
        line: BRING_REPLY[bringChoice],
        actions: [{ label: "Start with the address", primary: true, onClick: () => goTo("intake") }],
      };
    }
    if (view === "intake") {
      if (step === 1) {
        // The visitor's own address: wait for a pick, then check the owner, then read the building back.
        if (mode === "search") {
          if (!found) {
            if (lookup === "looking") return { placement: "form", pose: "thinking", line: ADDRESS_LOOKING, actions: [] };
            if (lookup === "empty") return { placement: "form", pose: "reassuring", line: ADDRESS_NOT_FOUND, actions: [] };
            if (lookup === "error") return { placement: "form", pose: "reassuring", line: ADDRESS_ERROR, actions: [] };
            return { placement: "form", pose: "listening", line: ADDRESS_START, actions: [] };
          }
          if (found.kind !== "public" && !found.accepted) {
            const accept = () => setAccepted(true);
            if (found.kind === "private") {
              return {
                placement: "form",
                pose: "reassuring",
                line: PRIVATE_BUILDING,
                actions: [{ label: "Go on anyway", primary: true, onClick: accept }, { label: "Try another address", onClick: resetSearch }],
              };
            }
            return {
              placement: "form",
              pose: "listening",
              line: unclearOwner(found.record?.ownername),
              actions: [{ label: "Yes, it's public", primary: true, onClick: accept }, { label: "No", onClick: resetSearch }],
            };
          }
        }
        const answered = confirm === "yes" ? null : confirm;
        if (!answered) {
          return {
            placement: "form",
            pose: "listening",
            line: mode === "search" && found ? foundLine(found.label, found.record?.ownername) : "I found it. This is what the city records say about the building. Is that right?",
            actions: [
              { label: "Yes, that's right", primary: true, onClick: () => { setConfirm("yes"); setStep(2); } },
              { label: "No, I want to edit", onClick: () => setConfirm("edit") },
              { label: "I don't know", onClick: () => setConfirm("unsure") },
            ],
          };
        }
        return { placement: "form", pose: answered === "unsure" ? "reassuring" : "listening", line: CONFIRM_REPLY[answered], actions: [] };
      }
      // When the city's records filled something in on this step, Fritts says so instead of the usual line.
      const filled =
        mode === "search" &&
        chosenPrefill !== null &&
        ((step === 2 && prefillOf(chosenPrefill, "annual_kwh")) ||
          (step === 3 && (prefillOf(chosenPrefill, "roof_area_sqft") || prefillOf(chosenPrefill, "roof_condition") || prefillOf(chosenPrefill, "existing_solar_kw"))));
      return { placement: "form", pose: step === 4 ? "explaining" : "listening", line: step === 4 && runProblem ? `${runProblem} Press Back to add it.` : filled ? PREFILL_STEP[step] : INTAKE_STEP[step], actions: [] };
    }
    if (view === "running") {
      if (runMode === "live" && live.status === "error") {
        return {
          placement: "stage",
          pose: "reassuring",
          line: live.message,
          actions: [
            { label: "Back to my answers", primary: true, onClick: () => goTo("intake") },
            { label: "Open a sample plan", onClick: () => goTo("home") },
          ],
        };
      }
      const current = runLines[Math.min(shownNow, runLines.length - 1)] ?? "";
      return { placement: "stage", pose: poseForStep(current), line: workingLine(current), actions: [] };
    }
    if (view === "ready") {
      return { placement: "center", pose: "present", line: readyLine(sample.outcome.label), actions: [{ label: "Open my report", primary: true, onClick: () => goTo("results") }] };
    }
    if (view === "results") {
      if (menu === "sections") {
        return {
          placement: "side",
          pose: "presenting",
          wide: true,
          line: "Which section would you like me to explain?",
          actions: [
            ...sample.plan.sections.map((s) => ({
              label: s.title,
              onClick: () => {
                const heart = s.claims.slice(0, 2).map((c) => firstSentence(plainify(c.text))).join(" ");
                setSaid(heart ? `Here's the heart of "${s.title}". ${heart} The full detail is in the report.` : `"${s.title}" has nothing to add beyond the report itself.`);
                setMenu("said");
              },
            })),
            { label: "Never mind", onClick: () => setMenu("menu") },
          ],
        };
      }
      if (menu === "said") {
        const copyAgain: GuideAction[] = shareUrl
          ? [{ label: "Copy link", primary: true, onClick: () => { void copyShareLink(sample.id).then(({ url, copied }) => setSaid(shareLine(url, copied))); } }]
          : [];
        return { placement: "side", pose: "presenting", line: said, actions: [...copyAgain, { label: "Anything else?", primary: !shareUrl, onClick: () => setMenu("menu") }] };
      }
      return {
        placement: "side",
        pose: "presenting",
        line: REPORT_MENU,
        actions: [
          { label: "Download PDF", onClick: () => { setShareUrl(null); setSaid(PDF_SAYS.making); setMenu("said"); void downloadPlanPdf(sample.plan).then((r) => setSaid(PDF_SAYS[r])); } },
          { label: "Share", onClick: () => { if (livePlan) { setShareUrl(null); setSaid(SHARE_LIVE); setMenu("said"); return; } void copyShareLink(sample.id).then(({ url, copied }) => { setShareUrl(url); setSaid(shareLine(url, copied)); setMenu("said"); }); } },
          { label: "Explain a section", primary: true, onClick: () => setMenu("sections") },
        ],
      };
    }
    return null;
  })();

  return (
    <div style={PALETTE} className="min-h-screen bg-[var(--fr-cream)] text-[var(--fr-ink)]">
      <TopBar onHome={() => goTo("home")} onStart={startExperience} />
      {view === "home" && <Home onPick={pick} onStart={startExperience} />}
      {view === "welcome" && <Backdrop eyebrow="Renewable energy planning for NYC public buildings" title="Professor Fritts" />}
      {view === "intake" && (
        <Intake
          sample={sample}
          mode={mode}
          found={found}
          prefill={chosenPrefill}
          values={values}
          onChange={(name, value) => setTyped((prev) => ({ ...prev, [name]: value }))}
          runProblem={runProblem}
          onBill={setBill}
          searchKey={searchKey}
          searchValue={searchValue}
          onPickAddress={pickAddress}
          onEditAddress={editAddress}
          onSearched={searched}
          onPickSample={pickSample}
          step={step}
          setStep={setStep}
          onRun={onRun}
        />
      )}
      {view === "running" && (
        <Running
          name={runMode === "live" ? (found?.label ?? "your building") : String(sample.profile.building_name)}
          lines={runLines}
          shown={shownNow}
          live={runMode === "live"}
          error={runMode === "live" && live.status === "error" ? live.message : null}
          onDone={() => goTo("ready")}
          onBack={() => goTo("intake")}
        />
      )}
      {view === "ready" && <Backdrop eyebrow="Your plan is ready" title={String(sample.profile.building_name ?? sample.label)} />}
      {view === "results" && (
        <div className="pb-56 lg:pb-0">
          <Results plan={sample} plans={PLANS} onRestart={() => goTo("home")} onPick={(id) => { setLivePlan(null); setSampleId(id); goTo("results"); }} />
        </div>
      )}
      {guide && <FrittsGuide placement={guide.placement} pose={guide.pose} line={guide.line} actions={guide.actions} wide={guide.wide} cue={cue} />}
    </div>
  );
}
