/**
 * Small shared pieces for the /plan-mockup pages: brand colors, number formatting, the label chip, cards and bars.
 * Kept in one file so the home, intake, running and results views all look the same.
 */
import type { CSSProperties, ReactNode } from "react";
import type { Range } from "./plan-types";

/** Brand colors, taken from the logo. Scoped to this page only (globals.css is untouched). */
export const PALETTE = {
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
export const LABELS: Record<string, { color: string; blurb: string }> = {
  FACT: { color: "#1c8c7e", blurb: "From a named source" },
  ESTIMATE: { color: "#2f6fb5", blurb: "Calculated, always shown as a range" },
  ASSUMPTION: { color: "#b7791f", blurb: "A stated starting point you can change" },
  RECOMMENDATION: { color: "#7a4fb0", blurb: "A suggested next step" },
};

// ------------------------------------------------------------------------------------------- formatting

export function money(n: number): string {
  const sign = n < 0 ? "-" : "";
  const v = Math.abs(n);
  if (v >= 1_000_000) return `${sign}$${(v / 1_000_000).toFixed(2).replace(/0+$/, "").replace(/\.$/, "")}M`;
  if (v >= 1000) return `${sign}$${Math.round(v / 1000).toLocaleString()}k`;
  return `${sign}$${Math.round(v).toLocaleString()}`;
}
export const moneyExact = (n: number) => `${n < 0 ? "-" : ""}$${Math.abs(Math.round(n)).toLocaleString()}`;
export const moneyRange = (r: Range) => (r[0] === r[1] ? money(r[0]) : `${money(r[0])} to ${money(r[1])}`);
export const moneyRangeExact = (r: Range) => (r[0] === r[1] ? moneyExact(r[0]) : `${moneyExact(r[0])} to ${moneyExact(r[1])}`);
export const pctRange = (r: Range) => (r[0] === r[1] ? `${r[0]}%` : `${r[0]}% to ${r[1]}%`);
export const yearsRange = (r: Range | null) => (r ? `${Math.round(r[0])} to ${Math.round(r[1])} years` : "not available");
export const hoursRange = (r: Range) => (r[1] <= 0 ? "None" : `${r[0]} to ${r[1]} hours`);

/** "roof_age_20_plus" becomes "Roof age 20 plus". */
export function nice(key: string): string {
  const s = key.replace(/_/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** A raw value as readable text: numbers with commas, true/false as Yes/No, lists joined, objects as compact JSON. */
export function show(value: unknown): string {
  if (value === null || value === undefined || value === "") return "none";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return Number.isInteger(value) ? value.toLocaleString() : String(Math.round(value * 10000) / 10000);
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.every((v) => typeof v !== "object") ? value.map(show).join(", ") : JSON.stringify(value);
  return JSON.stringify(value);
}

export const isWeb = (u: unknown): u is string => typeof u === "string" && /^https?:\/\//.test(u);

// ---------------------------------------------------------------------------------------------- pieces

export function Chip({ label, count }: { label: string; count?: number }) {
  const l = LABELS[label];
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold tracking-wide text-white" style={{ background: l?.color ?? "#555" }}>
      {label}
      {count != null ? <span className="opacity-80">· {count}</span> : null}
    </span>
  );
}

/** A horizontal bar showing a range on a 0..max scale, with an optional marker (the goal or the budget). */
export function RangeBar({ low, high, max, color, marker, markerLabel }: { low: number; high: number; max: number; color: string; marker?: number; markerLabel?: string }) {
  const left = Math.min(100, (low / max) * 100);
  const width = Math.max(1.5, Math.min(100 - left, ((high - low) / max) * 100));
  return (
    <div className="relative pt-5">
      {marker != null && (
        <div
          className={`absolute top-0 whitespace-nowrap text-[10px] font-medium text-[var(--fr-mute)] ${marker / max > 0.8 ? "-translate-x-full pr-1" : "-translate-x-1/2"}`}
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

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-[var(--fr-line)] bg-white p-5 shadow-[0_1px_0_rgba(18,48,61,0.04)] ${className}`}>{children}</div>;
}

export function SectionTitle({ eyebrow, title, sub }: { eyebrow?: string; title: string; sub?: string }) {
  return (
    <div className="mb-4">
      {eyebrow && <div className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--fr-teal)]">{eyebrow}</div>}
      <h2 className="text-2xl font-semibold text-[var(--fr-ink)]">{title}</h2>
      {sub && <p className="mt-1 max-w-2xl text-sm text-[var(--fr-mute)]">{sub}</p>}
    </div>
  );
}

/**
 * Text that may contain long web addresses: each address is replaced by a short "source" link, so a line like
 * "... since 2022, NYSERDA data https://data.ny.gov/very/long/path" reads "... since 2022 (source)".
 * A leading phrase such as "NYSERDA data" is kept as the link's label.
 */
export function LinkedText({ text }: { text: string }) {
  const urlPattern = /(?:(NYSERDA data|NYC DCAS[^,(]*?)\s*,?\s+)?(https?:\/\/[^\s),;]+)/g;
  const parts: ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;
  while ((match = urlPattern.exec(text)) !== null) {
    const before = text.slice(last, match.index).replace(/[,\s]+$/, "");
    if (before) parts.push(before);
    const label = match[1] ? match[1].trim() : "source";
    parts.push(
      <span key={match.index}>
        {" "}
        <a href={match[2]} target="_blank" rel="noreferrer" className="text-[var(--fr-teal)] underline">
          {label}
        </a>
      </span>,
    );
    last = match.index + match[0].length;
  }
  const rest = text.slice(last);
  if (rest) parts.push(rest);
  return <>{parts}</>;
}

/** A link that opens in a new tab, shown only for real web addresses. */
export function SourceLink({ url, children = "source" }: { url: unknown; children?: ReactNode }) {
  if (!isWeb(url)) return null;
  return (
    <a href={url} target="_blank" rel="noreferrer" className="text-[var(--fr-teal)] underline">
      {children}
    </a>
  );
}
