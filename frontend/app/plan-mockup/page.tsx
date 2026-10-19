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
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { AddressSearch } from "./AddressSearch";
import { buildingTypeLabel, fetchBuildingRecord, numberOf, ownerKind, type AddressSuggestion, type BuildingRecord, type FoundBuilding } from "./address";
import { FrittsGuide, type GuideAction, type GuideChatProps } from "./fritts/FrittsGuide";
import { poseForStep, type Placement, type PoseName } from "./fritts/poses";
import { planRun } from "./fritts/runPlan";
import { askPlanQuestion, getBuildingPrefill } from "@/lib/api";
import { LiveRunError, buildProfile, buildQuestion, goalNumbers, missingForRun, parseMoney, parseNumber, narrationFor as narrationForTools, planFromRun, runLive, stepsSoFar, type RunForm } from "./live-run";
import type { BuildingPrefill, PrefillItem, RunResponse } from "@/lib/types";
import { ADDRESS_ERROR, ADDRESS_LOOKING, ADDRESS_NOT_FOUND, ADDRESS_START, BRING, BRING_REPLY, CONFIRM_REPLY, HELLO, INTAKE_STEP, PDF_SAYS, PREFILL_STEP, PRIVATE_BUILDING, REPORT_MENU, SHARE_LIVE, foundLine, readyLine, shareLine, unclearOwner, workingLine } from "./fritts/script";
import { plainify } from "./plain";
import { copyShareLink, downloadPlanPdf } from "./plan-actions";
import { useDevView } from "./dev-view";
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

/** Helper to ensure smooth scrolling to a hash anchor even if the hash is already in the URL. */
function handleScrollToSection(id: string) {
  if (typeof window !== "undefined") {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  }
}

// ------------------------------------------------------------------------------------------------ top bar

function TopBar({ onStart }: { onStart: () => void }) {
  const [open, setOpen] = useState(false);
  const [devView, setDevView] = useDevView();
  // The developer menu stays out of sight: a small sun icon that opens only after three quick clicks (one or two do nothing),
  // so a visitor never stumbles on it. When it is open, one click closes it; Escape or a click elsewhere closes it too.
  const clicks = useRef(0);
  const clickTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const onSunClick = () => {
    if (open) {
      setOpen(false);
      return;
    }
    clicks.current += 1;
    if (clickTimer.current) clearTimeout(clickTimer.current);
    if (clicks.current >= 3) {
      clicks.current = 0;
      setOpen(true);
      return;
    }
    clickTimer.current = setTimeout(() => {
      clicks.current = 0;
    }, 900);
  };
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);
  return (
    <header className="sticky top-0 z-20 border-b border-[var(--fr-line)] bg-[var(--fr-cream)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-left">
          <Image src="/fritts-logo-mark.png" alt="Professor Fritts" width={525} height={575} className="h-9 w-auto rounded-sm" />
          <span>
            <span className="block text-base font-bold leading-tight text-[var(--fr-ink)]">Professor Fritts</span>
            <span className="block text-[11px] uppercase tracking-[0.16em] text-[var(--fr-teal)]">Renewable energy planning</span>
          </span>
        </Link>
        <nav className="ml-6 hidden items-center gap-5 text-sm text-[var(--fr-ink)] md:flex">
          <Link href="/" className="hover:text-[var(--fr-teal)]">Home</Link>
          <button type="button" onClick={onStart} className="hover:text-[var(--fr-teal)]">Plan a building</button>
          <Link href="/#samples" onClick={() => handleScrollToSection("samples")} className="hover:text-[var(--fr-teal)]">Sample plans</Link>
          <Link href="/#how" onClick={() => handleScrollToSection("how")} className="hover:text-[var(--fr-teal)]">How it works</Link>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <div className="relative" ref={menuRef}>
            <button type="button" onClick={onSunClick} aria-label="Developer tools" aria-expanded={open} className="rounded-full p-1.5 text-[var(--fr-mute)] opacity-40 transition hover:opacity-70">
              <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8" />
              </svg>
            </button>
            {open && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl border border-[var(--fr-line)] bg-white p-1 text-sm shadow-lg">
                <Link href="/dev/run-sequences" className="block rounded-lg px-3 py-2 hover:bg-[var(--fr-soft)]">
                  Run sequences <span className="block text-xs text-[var(--fr-mute)]">Test situations, live or scripted</span>
                </Link>
                <Link href="/planner" className="block rounded-lg px-3 py-2 hover:bg-[var(--fr-soft)]">
                  Classic planner <span className="block text-xs text-[var(--fr-mute)]">Form, chat, run log, roadmap</span>
                </Link>
                <label className="flex cursor-pointer items-start gap-2 rounded-lg px-3 py-2 hover:bg-[var(--fr-soft)]">
                  <input type="checkbox" checked={devView} onChange={(e) => setDevView(e.target.checked)} className="mt-1" />
                  <span>
                    Developer view <span className="block text-xs text-[var(--fr-mute)]">Show field names, flags and ids in reports</span>
                  </span>
                </label>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

// ------------------------------------------------------------------------------------------------- home

function Home({ onOpen, onRerun, onStart }: { onOpen: (id: string) => void; onRerun: (id: string) => void; onStart: () => void }) {
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
            <Link href="/#samples" onClick={() => handleScrollToSection("samples")} className="rounded-xl border border-[var(--fr-ink)] px-5 py-3 font-semibold text-[var(--fr-ink)] hover:bg-white">
              See a sample plan
            </Link>
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
          <SectionTitle eyebrow="Sample plans" title="See what you'd get" sub="Six real NYC buildings, one in each borough, planned from public data. Not every building gets a yes, and the plan says so honestly." />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {PLANS.map((s) => (
              <div key={s.id} className="flex h-full flex-col rounded-2xl border border-[var(--fr-line)] bg-white p-5 text-left transition hover:-translate-y-0.5 hover:shadow-lg">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                    style={{
                      // The colour comes with the answer: green is a clear yes, amber is a yes with a catch, blue is a step that comes first, red is not on this budget.
                      background: s.outcome.tone === "good" ? "#dff3ea" : s.outcome.tone === "caution" ? "#fdf0cf" : s.outcome.tone === "bad" ? "#f6d2cb" : "#e3ecf6",
                      color: s.outcome.tone === "bad" ? "#8a1f11" : "#12303d",
                    }}
                  >
                    {s.outcome.label}
                  </span>
                  <span className="text-[11px] text-[var(--fr-mute)]">{s.kind === "recorded" ? "From a real run" : "Scripted demo"}</span>
                </div>
                <div className="font-semibold text-[var(--fr-ink)]">{s.label}</div>
                {/* The goal and the question this building asked, as on the old run-list page. */}
                {s.profile.goal && <p className="mt-0.5 text-sm text-[var(--fr-mute)]">{String(s.profile.goal)}</p>}
                <p className="mt-3 text-sm leading-snug text-[var(--fr-ink)]">&ldquo;{s.question}&rdquo;</p>
                <p className="mt-3 border-t border-[var(--fr-line)] pt-3 text-xs text-[var(--fr-mute)]">{s.tag}</p>
                <div className="mt-auto flex items-center gap-3 pt-3">
                  <button type="button" onClick={() => onOpen(s.id)} className="text-sm font-medium text-[var(--fr-teal)] hover:underline">Open this plan →</button>
                  <button type="button" onClick={() => onRerun(s.id)} className="rounded-full border border-[var(--fr-ink)] px-3 py-1 text-sm font-medium text-[var(--fr-ink)] hover:bg-[var(--fr-ink)] hover:text-white">Rerun</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* The closing picture at the very bottom of the home page: Professor Fritts on a NYC rooftop. It is cropped to a shorter strip (keeping Fritts
          and the panels), and a short fade over the sky at its top blends it into the page colour so there is no hard line where the sample plans end. The fade stays above Fritts's head. */}
      <footer className="relative overflow-hidden bg-[var(--fr-soft)]">
        <Image
          src="/fritts/footer-banner.jpg"
          alt="Professor Fritts on a New York City rooftop with solar panels, planters and a rooftop battery"
          width={2172}
          height={724}
          sizes="100vw"
          className="block aspect-[5/2] w-full object-cover object-[78%_8%] sm:aspect-[4/1]"
        />
        <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-0 h-[17%]" style={{ backgroundImage: "linear-gradient(to bottom, var(--fr-soft) 0%, rgba(241,236,223,0.7) 40%, rgba(241,236,223,0) 100%)" }} />
      </footer>
    </>
  );
}

// ----------------------------------------------------------------------------------------------- intake

const STEPS = ["Find your building", "Energy and goals", "What you already have", "Your question"];

function Field({ label, value, hint, onChange, readOnly, placeholder }: { label: string; value: string | number | null | undefined; hint?: string; onChange?: (value: string) => void; readOnly?: boolean; placeholder?: string }) {
  const box = "mt-1 w-full rounded-lg border border-[var(--fr-line)] bg-white px-3 py-2 text-[var(--fr-ink)] outline-none focus:border-[var(--fr-teal)]";
  return (
    <label className="block">
      <span className="text-sm font-medium text-[var(--fr-ink)]">{label}</span>
      {onChange ? (
        // Typed into: the page keeps what was typed, so it can be sent to the planner.
        <input value={value ?? ""} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className={box} />
      ) : (
        <input defaultValue={value ?? ""} key={String(value)} readOnly={readOnly} placeholder={placeholder} className={box} />
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
  return { annual_kwh: text("annual_kwh"), floor_area_sqft: text("floor_area_sqft"), roof_area_sqft: text("roof_area_sqft"), existing_solar_kw: text("existing_solar_kw") };
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
  /** Throws away the visitor's edited question, so the one written from their answers shows again. */
  onResetQuestion: () => void;
}

function Intake({ sample, mode, found, prefill, values, onChange, onResetQuestion, runProblem, onBill, searchKey, searchValue, onPickAddress, onEditAddress, onSearched, onPickSample, step, setStep, onRun }: IntakeProps) {
  const searching = mode === "search";
  const rec = found?.record ?? null;
  // In search mode the form starts with only what the city's records say; in sample mode it is filled from the sample.
  const p: Record<string, string | number | null | undefined> = searching
    ? { address: found?.label, borough: found?.borough }
    : sample.profile;
  const pitched = String(p.roof_type ?? "").includes("pitch");
  // The question, written from the visitor's answers, and whether an edited version was written from different answers.
  const suggestedQuestion = buildQuestion(values);
  // What the question box shows: the visitor's edit if there is one, else the question written from their answers (or, for a saved sample, its own).
  const sampleEdited = !searching && values.sample_question_for === sample.id && values.sample_question !== undefined;
  const questionShown = searching ? (values.question !== undefined ? values.question : suggestedQuestion) : sampleEdited ? (values.sample_question ?? "") : sample.question;
  const questionStale = values.question !== undefined && values.question_base !== undefined && values.question_base !== suggestedQuestion;
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
            <div className="grid gap-3 sm:col-span-2 sm:grid-cols-3">
              <Field label="Cut grid power by (%)" value={searching ? values.goal_percent : p.goal_percent} onChange={searching ? (v) => onChange("goal_percent", v) : undefined} />
              <Field label="By year" value={searching ? values.target_year : p.target_year} onChange={searching ? (v) => onChange("target_year", v) : undefined} />
              <Field label="Backup hours needed" value={searching ? values.backup_hours_wanted : p.backup_hours_wanted} onChange={searching ? (v) => onChange("backup_hours_wanted", v) : undefined} placeholder="Optional" />
            </div>
            <div className="sm:col-span-2"><Field label="Anything that must keep running in an outage?" value={searching ? values.critical_loads : (p.critical_loads ?? "")} onChange={searching ? (v) => onChange("critical_loads", v) : undefined} /></div>
            {/* The question, written from the answers above. The visitor can add to it or edit it here; the last step then shows the final
                question as a quote. A saved sample shows the question it was recorded with, locked, because a saved plan answers that one. */}
            <div className="sm:col-span-2">
              <label htmlFor="your-question" className="text-sm font-medium text-[var(--fr-ink)]">Your question for Professor Fritts</label>
              <textarea
                id="your-question"
                rows={4}
                maxLength={500}
                value={questionShown}
                onChange={(e) => {
                  if (searching) {
                    if (values.question === undefined) onChange("question_base", suggestedQuestion);
                    onChange("question", e.target.value);
                  } else {
                    onChange("sample_question_for", sample.id);
                    onChange("sample_question", e.target.value);
                  }
                }}
                className="mt-1 w-full rounded-lg border border-[var(--fr-line)] bg-white px-3 py-2 text-[var(--fr-ink)] outline-none focus:border-[var(--fr-teal)]"
              />
              <div className="mt-1 flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--fr-mute)]">
                <span>Written from your answers above. Add your own context or change the wording, for example: &ldquo;Our rec center flooded in Hurricane Sandy and is a cooling center.&rdquo;</span>
                <span>{questionShown.length}/500</span>
              </div>
              {searching && questionStale && <p className="mt-1 text-xs text-[var(--fr-warn)]">Your goal, budget or what must keep running changed since you edited this question. Reset to update it.</p>}
              {(searching ? values.question !== undefined : sampleEdited) && (
                <button type="button" onClick={onResetQuestion} className="mt-1 text-xs font-semibold text-[var(--fr-teal)] underline">Reset the question</button>
              )}
            </div>
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
            {/* The last step only shows the final question and a few points, then the visitor runs it. The question is edited on the
                Energy and goals step (a saved sample shows the question it was recorded with). */}
            <p className="text-sm text-[var(--fr-mute)]">Here&rsquo;s the question we&rsquo;ll answer:</p>
            <blockquote className="rounded-xl border-l-4 border-[var(--fr-gold)] bg-[var(--fr-soft)] p-4 text-[var(--fr-ink)]">&ldquo;{searching ? (values.question?.trim() ? values.question.trim() : suggestedQuestion) : sample.question}&rdquo;</blockquote>
            {searching ? (
              <>
                <div className="grid gap-1.5 text-sm text-[var(--fr-ink)] sm:grid-cols-2">
                  <Found>{found?.label ?? "No address chosen yet"}</Found>
                  {rec && <Found>{buildingTypeLabel(rec)}</Found>}
                  {parseMoney(values.budget_amount) !== null && <Found>${parseMoney(values.budget_amount)?.toLocaleString()} capital budget</Found>}
                  {parseNumber(values.annual_kwh) !== null && <Found>{parseNumber(values.annual_kwh)?.toLocaleString()} kWh a year</Found>}
                  {goalNumbers(values).percent !== null && <Found>Cut grid electricity {goalNumbers(values).percent}%{goalNumbers(values).year ? ` by ${goalNumbers(values).year}` : ""}</Found>}
                </div>
                <p className="rounded-xl bg-[var(--fr-soft)] p-3 text-xs text-[var(--fr-mute)]">
                  Pressing Run starts a real analysis of this building. It takes about two minutes, and it uses your answers and the city&rsquo;s public records.
                </p>
                {runProblem && <p className="rounded-xl border border-[var(--fr-gold)] bg-white p-3 text-sm text-[var(--fr-ink)]">{runProblem}</p>}
              </>
            ) : (
              <div className="grid gap-1.5 text-sm text-[var(--fr-ink)] sm:grid-cols-2">
                <Found>{String(p.building_name)}</Found>
                <Found>${Number(p.budget_amount).toLocaleString()} capital budget</Found>
                <Found>{Number(p.annual_kwh).toLocaleString()} kWh a year</Found>
                <Found>{String(p.goal)}</Found>
              </div>
            )}
          </div>
        )}

        <div className="mt-6 flex items-center justify-between">
          <button type="button" disabled={step === 1} onClick={() => setStep(step - 1)} className="rounded-lg px-3 py-2 text-sm text-[var(--fr-ink)] disabled:opacity-30">← Back</button>
          {step < 4 ? (
            <button type="button" disabled={!canContinue} onClick={() => setStep(step + 1)} className="rounded-xl bg-[var(--fr-ink)] px-5 py-2.5 font-semibold text-white disabled:opacity-40">Continue</button>
          ) : (
            <button type="button" onClick={onRun} className="rounded-xl bg-[var(--fr-teal)] px-5 py-2.5 font-semibold text-white">Ask Professor Fritts</button>
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
  chat?: GuideChatProps;
}

function PlanMockupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const viewParam = searchParams.get("view");
  const view: View =
    viewParam && ["home", "welcome", "intake", "running", "ready", "results"].includes(viewParam)
      ? (viewParam as View)
      : "home";

  const sampleParam = searchParams.get("sample");
  const [selectedSampleId, setSelectedSampleId] = useState<string>(() => {
    if (sampleParam && PLANS.some((x) => x.id === sampleParam)) return sampleParam;
    return PLANS[0]?.id ?? "";
  });
  const sampleId = sampleParam && PLANS.some((x) => x.id === sampleParam) ? sampleParam : selectedSampleId;
  const setSampleId = setSelectedSampleId;

  const stepParam = searchParams.get("step");
  const [selectedStep, setSelectedStep] = useState<number>(() => {
    const st = Number(stepParam);
    return st >= 1 && st <= 4 ? st : 1;
  });
  const stepFromParam = Number(stepParam);
  const step = stepFromParam >= 1 && stepFromParam <= 4 ? stepFromParam : selectedStep;
  const setStep = setSelectedStep;

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
  const [chatBusy, setChatBusy] = useState(false);
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  // The share link Fritts last copied, so his menu can offer "Copy link" again.
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const [prevSampleKey, setPrevSampleKey] = useState(sampleId);
  const currentSampleKey = livePlan ? livePlan.id : sampleId;
  if (currentSampleKey !== prevSampleKey) {
    setPrevSampleKey(currentSampleKey);
    setChatHistory([]);
    setSaid("");
    setMenu("menu");
  }
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
  const values: RunForm = { goal_percent: "30", target_year: "2030", ...suggestedFrom(chosenPrefill), ...typed };

  /** Navigates between screens using Next.js routing. */
  const navigate = useCallback(
    (v: View, extra?: { sample?: string; step?: number }, replace = false) => {
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

      const params = new URLSearchParams();
      if (v !== "home") {
        params.set("view", v);
      }
      if (extra?.sample) {
        params.set("sample", extra.sample);
        setSelectedSampleId(extra.sample);
      } else if (v === "results" && sampleId) {
        params.set("sample", sampleId);
      }
      if (extra?.step && extra.step > 1) {
        params.set("step", String(extra.step));
        setSelectedStep(extra.step);
      }
      const qs = params.toString();
      const target = qs ? `/?${qs}` : "/";
      if (replace) {
        router.replace(target, { scroll: true });
      } else {
        router.push(target, { scroll: true });
      }
    },
    [router, sampleId]
  );

  useEffect(() => {
    // Leaving for the home page, the welcome or the form stops following a real run that is still going.
    if (view === "home" || view === "welcome" || view === "intake") liveToken.current += 1;
    if (typeof window !== "undefined") window.scrollTo({ top: 0 });
  }, [view]);

  // The working list plays itself, each step lasting as long as its part of Fritts's scene, then the report is ready.
  useEffect(() => {
    if (view !== "running" || runMode !== "sample") return;
    if (runShown >= runLines.length) {
      const t = setTimeout(() => navigate("ready"), 900);
      return () => clearTimeout(t);
    }
    // Each step lasts until the next one starts, so every scene of Fritts plays one full pass of its animation.
    const stepEnd = savedRunPlan.starts[runShown + 1] ?? savedRunPlan.total;
    const t = setTimeout(() => setRunShown((n) => n + 1), stepEnd - savedRunPlan.starts[runShown]);
    return () => clearTimeout(t);
  }, [view, runMode, runShown, runLines.length, savedRunPlan, navigate]);

  /** Starts a real analysis for the building the visitor chose and follows it to the end. */
  const startLiveRun = async (building: FoundBuilding) => {
    const question = values.question?.trim() ? values.question.trim() : buildQuestion(values);
    const mine = ++liveToken.current;
    setRunMode("live");
    setLivePlan(null);
    setLive({ status: "running", run: null, message: "" });
    navigate("running");
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
      navigate("ready");
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
    navigate("running");
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
    navigate("welcome");
  };
  /** "Open this plan" on a sample card: straight to that plan's finished report. */
  const openPlan = (id: string) => {
    setLivePlan(null);
    setSampleId(id);
    setMode("sample");
    setRunMode("sample");
    navigate("results", { sample: id });
  };
  /** "Rerun" on a sample card: plays the recorded run again, step by step with Fritts at work, then offers the report. */
  const rerunPlan = (id: string) => {
    setLivePlan(null);
    setSampleId(id);
    setMode("sample");
    setRunMode("sample");
    navigate("running");
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
        actions: [{ label: "Start with the address", primary: true, onClick: () => navigate("intake") }],
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
            { label: "Back to my answers", primary: true, onClick: () => navigate("intake") },
            { label: "Open a sample plan", onClick: () => navigate("home") },
          ],
        };
      }
      const current = runLines[Math.min(shownNow, runLines.length - 1)] ?? "";
      return { placement: "stage", pose: poseForStep(current), line: workingLine(current), actions: [] };
    }
    if (view === "ready") {
      return { placement: "center", pose: "present", line: readyLine(sample.outcome.label), actions: [{ label: "Open my report", primary: true, onClick: () => navigate("results") }] };
    }
    if (view === "results") {
      const handleChatSend = async (question: string) => {
        setChatBusy(true);
        setShareUrl(null);
        setMenu("said");
        setSaid("Thinking… let me look into that in your plan.");
        try {
          const reply = await askPlanQuestion(
            sample.plan as unknown as Record<string, unknown>,
            question,
            chatHistory
          );
          setChatHistory((prev) => [
            ...prev,
            { role: "user", content: question },
            { role: "assistant", content: reply },
          ]);
          setSaid(reply);
        } catch {
          setSaid("I had trouble checking that just now. Please try asking again.");
        } finally {
          setChatBusy(false);
        }
      };

      const pills = [
        {
          label: "📥 Download PDF",
          onClick: () => {
            setShareUrl(null);
            setSaid(PDF_SAYS.making);
            setMenu("said");
            void downloadPlanPdf(sample.plan).then((r) => setSaid(PDF_SAYS[r]));
          },
        },
        {
          label: "🔍 Explain a section",
          onClick: () => setMenu("sections"),
        },
        {
          label: "✏️ What info is needed next?",
          onClick: () => {
            void handleChatSend("What missing information or professional verifications do we need next to make this plan actionable?");
          },
        },
        {
          label: "💡 Reduce upfront cost",
          onClick: () => {
            void handleChatSend("How can we reduce the upfront capital cost or improve payback for this building?");
          },
        },
      ];

      const chatConfig: GuideChatProps = {
        onSend: handleChatSend,
        busy: chatBusy,
        placeholder: "Ask Claude about this plan…",
        pills,
      };

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
          chat: chatConfig,
        };
      }
      if (menu === "said") {
        const copyAgain: GuideAction[] = shareUrl
          ? [{ label: "Copy link", primary: true, onClick: () => { void copyShareLink(sample.id).then(({ url, copied }) => setSaid(shareLine(url, copied))); } }]
          : [{ label: "Share", onClick: () => { if (livePlan) { setShareUrl(null); setSaid(SHARE_LIVE); return; } void copyShareLink(sample.id).then(({ url, copied }) => { setShareUrl(url); setSaid(shareLine(url, copied)); }); } }];
        return {
          placement: "side",
          pose: chatBusy ? "thinking" : "presenting",
          wide: true,
          line: said,
          actions: [...copyAgain, { label: "Overview", primary: !shareUrl, onClick: () => { setSaid(""); setMenu("menu"); } }],
          chat: chatConfig,
        };
      }
      return {
        placement: "side",
        pose: chatBusy ? "thinking" : "presenting",
        wide: true,
        line: REPORT_MENU,
        actions: [
          { label: "Share", onClick: () => { if (livePlan) { setShareUrl(null); setSaid(SHARE_LIVE); setMenu("said"); return; } void copyShareLink(sample.id).then(({ url, copied }) => { setShareUrl(url); setSaid(shareLine(url, copied)); setMenu("said"); }); } },
        ],
        chat: chatConfig,
      };
    }
    return null;
  })();

  return (
    <div style={PALETTE} className="min-h-screen bg-[var(--fr-cream)] text-[var(--fr-ink)]">
      <TopBar onStart={startExperience} />
      {view === "home" && <Home onOpen={openPlan} onRerun={rerunPlan} onStart={startExperience} />}
      {view === "welcome" && <Backdrop eyebrow="Renewable energy planning for NYC public buildings" title="Professor Fritts" />}
      {view === "intake" && (
        <Intake
          sample={sample}
          mode={mode}
          found={found}
          prefill={chosenPrefill}
          values={values}
          onChange={(name, value) => setTyped((prev) => ({ ...prev, [name]: value }))}
          onResetQuestion={() => setTyped((prev) => Object.fromEntries(Object.entries(prev).filter(([name]) => !["question", "question_base", "sample_question", "sample_question_for"].includes(name))))}
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
          onDone={() => navigate("ready")}
          onBack={() => navigate("intake")}
        />
      )}
      {view === "ready" && <Backdrop eyebrow="Your plan is ready" title={String(sample.profile.building_name ?? sample.label)} />}
      {view === "results" && (
        <div className="pb-56 lg:pb-0">
          <Results plan={sample} plans={PLANS} onRestart={() => navigate("home")} onPick={(id) => { setLivePlan(null); setSampleId(id); navigate("results", { sample: id }); }} />
        </div>
      )}
      {guide && <FrittsGuide placement={guide.placement} pose={guide.pose} line={guide.line} actions={guide.actions} wide={guide.wide} cue={cue} chat={guide.chat} />}
    </div>
  );
}

export default function PlanMockup() {
  return (
    <Suspense fallback={null}>
      <PlanMockupContent />
    </Suspense>
  );
}
