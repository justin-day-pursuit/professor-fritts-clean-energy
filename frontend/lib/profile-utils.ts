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

/**
 * Fields the live tools cannot work without: the solar lookup needs the address and borough
 * to find the building and the roof area to size the array. To require another field, add a
 * row here and a "*" on its label in intake-form.tsx.
 */
const REQUIRED_FIELDS: { label: string; value: (p: IntakeProfile) => unknown }[] = [
  { label: "Address", value: (p) => p.address },
  { label: "Borough or county", value: (p) => p.borough || p.county },
  { label: "Roof area (a number above 0)", value: validRoofArea },
];

/** Labels of required intake fields that are still empty; an empty list means the form can be sent. */
export function missingRequiredFields(profile: IntakeProfile): string[] {
  return REQUIRED_FIELDS.filter(({ value }) => String(value(profile) ?? "").trim() === "").map(
    ({ label }) => label,
  );
}

export function emptyProfile(): IntakeProfile {
  return { state: "NY", budget_type: "capital" };
}
