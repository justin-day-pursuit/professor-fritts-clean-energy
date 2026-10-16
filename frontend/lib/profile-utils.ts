/**
 * Helpers to turn intake form values into the profile JSON the backend expects.
 */
import type { IntakeProfile } from "@/lib/types";

const NUMERIC_KEYS: (keyof IntakeProfile)[] = [
  "floor_area_sqft",
  "year_built",
  "roof_area_sqft",
  "roof_replaced_year",
  "annual_kwh",
  "budget_amount",
  "budget_year",
  "target_year",
  "critical_load_hours",
  "critical_load_kw",
  "backup_hours_wanted",
  "goal_percent",
  "lighting_retrofit_year",
  "verified_usable_roof_sqft",
  "existing_solar_kw",
  "existing_solar_kwh",
];

/**
 * Turns a form field (typed text, including commas) into a number for the
 * profile JSON the backend expects. Empty or non-numeric becomes undefined so
 * profileToApi omits that key. If a field should stay a string, remove it from
 * NUMERIC_KEYS above instead of changing this helper.
 */
function coerceNumber(value: string | number | undefined): number | undefined {
  if (value === undefined || value === "") return undefined;
  if (typeof value === "number") return value;
  const n = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(n) ? n : undefined;
}

/** Build a profile object from form state, dropping empty strings. */
export function profileToApi(profile: IntakeProfile): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, raw] of Object.entries(profile)) {
    if (raw === undefined || raw === "") continue;
    if (NUMERIC_KEYS.includes(key as keyof IntakeProfile)) {
      const num = coerceNumber(raw as string | number);
      if (num !== undefined) out[key] = num;
    } else {
      out[key] = raw;
    }
  }
  return out;
}

/** Map GET /api/sessions profile JSON into form fields. */
export function apiToProfile(data: Record<string, unknown>): IntakeProfile {
  const profile: IntakeProfile = {};
  for (const [key, value] of Object.entries(data)) {
    if (key.startsWith("_")) continue;
    (profile as Record<string, unknown>)[key] = value as string | number;
  }
  return profile;
}

/**
 * Roof area as the backend will see it: a number above zero, or "" when the box is empty, text
 * (profileToApi drops non-numeric values), zero or negative. Keeps text like "abc" from passing
 * the send guard and then arriving with no roof area at all.
 */
function validRoofArea(profile: IntakeProfile): number | "" {
  const n = coerceNumber(profile.roof_area_sqft);
  return n !== undefined && n > 0 ? n : "";
}

/** The five NYC boroughs: the only places the planner covers. Used by the intake form pick-list. */
export const NYC_BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"] as const;

/**
 * Fields the live tools cannot work without: the solar lookup needs the address and borough
 * to find the building and the roof area to size the array. To require another field, add a
 * row here and a "*" on its label in intake-form.tsx.
 */
const REQUIRED_FIELDS: { label: string; value: (p: IntakeProfile) => unknown }[] = [
  { label: "Address", value: (p) => p.address },
  { label: "Borough", value: (p) => p.borough || p.county },
  { label: "Roof area (a number above 0)", value: validRoofArea },
];

/** Labels of required intake fields that are still empty; an empty list means the form can be sent. */
export function missingRequiredFields(profile: IntakeProfile): string[] {
  return REQUIRED_FIELDS.filter(({ value }) => String(value(profile) ?? "").trim() === "").map(
    ({ label }) => label,
  );
}

export function emptyProfile(): IntakeProfile {
  return { state: "NY", budget_type: "capital", goal_percent: DEFAULT_GOAL_PERCENT };
}

/**
 * The roof types the intake offers. The backend reads this text to decide whether a roof is flat:
 * anything but "flat" is not sized from the flat-roof defaults until an engineer or roofer has
 * verified the usable area (see backend/tools/roof.py). To add a type, add a row here and, if it is
 * not flat, nothing else: the backend treats every word it does not know as "unknown", which is
 * still sized as flat, so a new non-flat type also needs its word added to NON_FLAT_WORDS there.
 */
export const ROOF_TYPES = [
  { value: "flat", label: "Flat" },
  { value: "pitched", label: "Pitched or sloped" },
  { value: "mixed", label: "Flat and pitched" },
  { value: "other", label: "Dome, tower or other" },
] as const;

/** True when the chosen roof type is one the planner does not size like a flat roof. */
export function isNotFlat(roofType: string | undefined): boolean {
  return roofType === "pitched" || roofType === "mixed" || roofType === "other";
}

/** The goal percent the form starts with, and the quick-pick presets under the slider. */
export const DEFAULT_GOAL_PERCENT = 30;
export const GOAL_PRESETS = [10, 20, 30, 50] as const;

/** Added to every optional pick-list so a user is never forced to guess. The backend treats "unknown" as blank. */
const DONT_KNOW = { value: "unknown", label: "Don't know" } as const;

/**
 * Pick-lists for the optional intake questions. The values are what the backend reads (see
 * backend/agent/notes.py, _record_intake_details, and agent/checks.py, _intake_detail_issues), so
 * change a value there and here together. A new option only needs a row here.
 */
export const OWNER_AGENCIES = [
  { value: "doe", label: "NYC Department of Education (public school)" },
  { value: "parks", label: "NYC Parks" },
  { value: "hhc", label: "NYC Health + Hospitals" },
  { value: "nycha", label: "NYCHA" },
  { value: "other_city", label: "Other city agency" },
  { value: "other", label: "Other" },
  DONT_KNOW,
] as const;

export const ROOF_CONDITIONS = [
  { value: "good", label: "Good (under about 10 years old)" },
  { value: "fair", label: "Fair" },
  { value: "poor", label: "Poor or near the end of its life" },
  DONT_KNOW,
] as const;

export const LIGHTING_TYPES = [
  { value: "led_all", label: "All LED" },
  { value: "led_partial", label: "Some LED" },
  { value: "fluorescent", label: "Mostly fluorescent" },
  { value: "incandescent_mixed", label: "Incandescent or mixed" },
  DONT_KNOW,
] as const;

export const HEATING_FUELS = [
  { value: "electric", label: "Electric" },
  { value: "natural_gas", label: "Natural gas" },
  { value: "oil", label: "Oil" },
  { value: "steam", label: "District steam" },
  { value: "mixed", label: "Mixed" },
  DONT_KNOW,
] as const;

export const COOLING_TYPES = [
  { value: "central_ac", label: "Central air conditioning" },
  { value: "window_units", label: "Window units" },
  { value: "none", label: "No cooling" },
  DONT_KNOW,
] as const;

export const YES_NO = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
  DONT_KNOW,
] as const;

export const GOAL_TYPES = [
  { value: "percent_reduction", label: "Cut grid electricity by a percent" },
  { value: "cost_savings", label: "Lower energy bills" },
  { value: "resilience", label: "Backup power in outages" },
  { value: "net_zero", label: "Net zero or fully renewable" },
] as const;
