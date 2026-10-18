/**
 * Plain-language labels for the data the plan page shows.
 *
 * The backend returns records with code-style field names (footprint_total_sqft, site_eui_kbtu_per_sqft). A facilities
 * manager should never see those, so each known field gets a plain label and, where it helps, a unit and a formatter. A field
 * not listed here falls back to its name in words, so new data still appears. The "Developer view" switch on the page shows
 * the raw names beside the plain ones.
 */
import { show } from "./ui";

export interface FieldInfo {
  label: string;
  /** Turns the raw value into text; defaults to the generic formatter. */
  fmt?: (v: unknown) => string;
  /** Hidden in the normal view (shown only in the developer view): ids, internal errors, duplicated links. */
  internal?: boolean;
}

const num = (v: unknown, unit = "", digits = 0) =>
  typeof v === "number" ? `${v.toLocaleString(undefined, { maximumFractionDigits: digits })}${unit}` : show(v);
const usdPerKwh = (v: unknown) => (typeof v === "number" ? `$${v.toFixed(4).replace(/0+$/, "").replace(/\.$/, "")} per kWh` : show(v));
const yesNo = (v: unknown) => (v === true ? "Yes" : v === false ? "No" : show(v));
const percentPair = (v: unknown) =>
  Array.isArray(v) && v.length === 2 && v.every((x) => typeof x === "number") ? `${Math.round(v[0] * 100)}% to ${Math.round(v[1] * 100)}%` : show(v);
const sqftList = (v: unknown) => (Array.isArray(v) ? v.map((x) => (typeof x === "number" ? `${x.toLocaleString()} sq ft` : show(x))).join(", ") : show(v));
const tidyKey = (v: unknown) => {
  const s = typeof v === "string" ? v.replace(/_/g, " ") : show(v);
  return s.charAt(0).toUpperCase() + s.slice(1);
};

export const FIELDS: Record<string, FieldInfo> = {
  // what you entered
  address: { label: "Address" },
  borough: { label: "Borough" },
  city: { label: "City" },
  state: { label: "State" },
  building_name: { label: "Building name" },
  building_type: { label: "Building type", fmt: tidyKey },
  contact_name: { label: "Contact" },
  floor_area_sqft: { label: "Floor area", fmt: (v) => num(v, " sq ft") },
  year_built: { label: "Year built", fmt: (v) => String(v) },
  roof_type: { label: "Roof type", fmt: tidyKey },
  roof_area_sqft: { label: "Roof area", fmt: (v) => num(v, " sq ft") },
  roof_replaced_year: { label: "Roof last replaced", fmt: (v) => String(v) },
  utility: { label: "Utility" },
  annual_kwh: { label: "Electricity used per year", fmt: (v) => num(v, " kWh") },
  budget_amount: { label: "Budget", fmt: (v) => (typeof v === "number" ? `$${v.toLocaleString()}` : show(v)) },
  budget_year: { label: "Budget year", fmt: (v) => String(v) },
  budget_type: { label: "Budget type", fmt: tidyKey },
  goal: { label: "Goal" },
  goal_percent: { label: "Goal: cut grid electricity by", fmt: (v) => `${v}%` },
  electricity_rate_usd_per_kwh: { label: "Your electricity price", fmt: usdPerKwh },
  target_year: { label: "Target year", fmt: (v) => String(v) },
  critical_loads: { label: "What must keep running in an outage" },
  critical_load_kw: { label: "Power those loads draw", fmt: (v) => num(v, " kW") },
  backup_hours_wanted: { label: "Hours of backup wanted", fmt: (v) => num(v, " hours") },
  existing_renewables: { label: "Other renewable systems" },
  existing_efficiency: { label: "Efficiency work already done" },
  existing_solar_kw: { label: "Solar already on the roof", fmt: (v) => num(v, " kW") },
  profile_flags: { label: "Notes on your entries", internal: true },
  question: { label: "Question asked", internal: true },

  // city tax-lot and footprint record
  bbl: { label: "Tax lot number (BBL)", fmt: (v) => String(v) },
  zipcode: { label: "ZIP code", fmt: (v) => String(v) },
  gross_floor_area_sqft: { label: "Floor area in the city record", fmt: (v) => num(v, " sq ft") },
  lot_area_sqft: { label: "Lot size", fmt: (v) => num(v, " sq ft") },
  num_floors: { label: "Floors" },
  building_class: { label: "City building class" },
  land_use_code: { label: "City land-use code" },
  landmark_flag: { label: "Landmark or historic district", fmt: yesNo },
  lot_matches_intake_floor: { label: "Lot size fits your floor area", fmt: yesNo },
  footprint_total_sqft: { label: "Building outline on the lot (ground area)", fmt: (v) => num(v, " sq ft") },
  footprint_building_count: { label: "Buildings on the lot" },
  footprint_buildings_sqft: { label: "Size of each building outline", fmt: sqftList },
  geocoder_match: { label: "Address matched to" },
  footprints_error: { label: "Footprint lookup problem", internal: true },
  city_energy_errors: { label: "Energy record lookup problems", internal: true },
  footprints_source_url: { label: "Footprint source", internal: true },
  ll84_source_url: { label: "Energy report source", internal: true },
  ll24_source_url: { label: "Roof assessment source", internal: true },
  query: { label: "Search used", internal: true },

  // city energy report (Local Law 84)
  property_name: { label: "Name in the city's energy report" },
  property_type: { label: "Property type in the energy report" },
  report_year: { label: "Report year", fmt: (v) => String(v) },
  electricity_kwh: { label: "Electricity used", fmt: (v) => num(v, " kWh") },
  natural_gas_kbtu: { label: "Natural gas used", fmt: (v) => num(v, " thousand BTU") },
  fuel_oil_kbtu: { label: "Fuel oil used", fmt: (v) => num(v, " thousand BTU") },
  district_steam_kbtu: { label: "Steam used", fmt: (v) => num(v, " thousand BTU") },
  site_eui_kbtu_per_sqft: { label: "Energy use per square foot", fmt: (v) => num(v, " thousand BTU per sq ft", 1) },
  weather_normalized_site_eui: { label: "Energy use per sq ft, adjusted for weather", fmt: (v) => num(v, " thousand BTU per sq ft", 1) },
  energy_star_score: { label: "ENERGY STAR score (1 to 100)" },

  // city roof assessment (Local Law 24)
  agency: { label: "Owning agency" },
  site: { label: "Site name" },
  status: { label: "Solar readiness status" },
  solar_ready: { label: "Solar ready", fmt: yesNo },
  roof_condition: { label: "Roof condition (city's rating)" },
  roof_age: { label: "Roof age (city's rating)" },
  installed_kw: { label: "Solar installed or planned", fmt: (v) => num(v, " kW", 1) },
  estimated_annual_production_kwh: { label: "Estimated yearly solar output", fmt: (v) => num(v, " kWh") },
  upfront_project_cost_usd: { label: "Solar project cost", fmt: (v) => (typeof v === "number" ? `$${v.toLocaleString()}` : show(v)) },
  financing_mechanism: { label: "How it was financed" },
  city_council_district: { label: "City Council district" },

  // what the plan noticed about the site
  roof_kind: { label: "Roof shape", fmt: (v) => (v === "flat" ? "Flat" : v === "non_flat" ? "Not flat" : tidyKey(v)) },
  city_not_solar_ready: { label: "City says the roof is not solar ready", fmt: yesNo },
  roof_age_20_plus: { label: "Roof is 20 years old or more", fmt: yesNo },
  owner_agency: { label: "Owner", fmt: (v) => (v === "doe" ? "NYC Department of Education" : tidyKey(v)) },
  flood_zone: { label: "FEMA flood zone" },
  parkland: { label: "On parkland", fmt: yesNo },
  landmark: { label: "Landmark", fmt: yesNo },
  existing_systems: { label: "Systems already on the building" },
  verified_usable_roof_sqft: { label: "Roof area checked by a professional", fmt: (v) => num(v, " sq ft") },

  // energy use and goal
  source: { label: "Where the figure came from" },
  goal_kwh: { label: "Goal, in energy", fmt: (v) => num(v, " kWh a year") },

  // solar output (PVWatts)
  annual_ac_kwh: { label: "Yearly solar output (central)", fmt: (v) => num(v, " kWh") },
  annual_ac_kwh_low: { label: "Yearly solar output (low)", fmt: (v) => num(v, " kWh") },
  annual_ac_kwh_high: { label: "Yearly solar output (high)", fmt: (v) => num(v, " kWh") },
  system_kw_dc: { label: "Array size", fmt: (v) => num(v, " kW", 1) },
  capacity_factor: { label: "Share of the year the array runs at full power", fmt: (v) => (typeof v === "number" ? `${v}%` : show(v)) },
  solar_radiation_kwh_m2_day: { label: "Sunshine per day", fmt: (v) => num(v, " kWh per square meter", 2) },
  monthly_ac_kwh: { label: "Output by month (Jan to Dec, kWh)", fmt: (v) => (Array.isArray(v) ? v.map((x) => (typeof x === "number" ? Math.round(x).toLocaleString() : x)).join(", ") : show(v)) },
  range_assumption: { label: "Why there is a low and a high figure" },
  weather_data_source: { label: "Weather data used" },
  location: { label: "Location used", fmt: (v) => (v && typeof v === "object" ? String((v as Record<string, unknown>).label ?? "") : show(v)) },
  pvwatts_inputs: { label: "Settings used for the solar estimate", internal: true },

  // electricity price
  avg_energy_charge_usd_per_kwh: { label: "Average price (12 months)", fmt: usdPerKwh },
  price_low_usd_per_kwh: { label: "Price, low end", fmt: usdPerKwh },
  price_high_usd_per_kwh: { label: "Price, high end", fmt: usdPerKwh },
  latest_month_usd_per_kwh: { label: "Price in the latest month", fmt: usdPerKwh },
  latest_month: { label: "Latest month" },
  months_averaged: { label: "Months averaged" },
  period_start: { label: "Average starts" },
  effective_date: { label: "Effective" },
  price_units: { label: "Price unit", internal: true },
  tariff_name: { label: "Price source" },
  needs_user_confirmation: { label: "Needs your confirmation", fmt: yesNo },
  note: { label: "Note" },

  // battery
  battery_kw: { label: "Battery power", fmt: (v) => num(v, " kW", 1) },
  battery_kwh: { label: "Battery energy storage", fmt: (v) => num(v, " kWh") },
  critical_load_hours: { label: "Hours of backup", fmt: (v) => num(v, " hours", 1) },
  notes: { label: "How it was sized" },

  // flood and hazards
  special_flood_hazard_area: { label: "High-risk flood area", fmt: yesNo },
  zone_subtype: { label: "Flood zone detail" },

  // calculation records
  value: { label: "Result" },
  units: { label: "Unit" },
  formula: { label: "Formula (as coded)", internal: true },
  plain_formula: { label: "How it is worked out" },
  name: { label: "Calculation" },
  calc_id: { label: "Calculation id", internal: true },
  assumption_ids: { label: "Assumptions used", internal: true },
  inputs: { label: "Numbers used" },
  label: { label: "Kind of figure", internal: true },
  efficiency_savings_realization: { label: "Share of predicted efficiency savings counted", fmt: percentPair },
};

/** The plain label for a field, or its raw name written in words when it isn't listed. */
export function fieldLabel(key: string): string {
  return FIELDS[key]?.label ?? tidyKey(key);
}

/** The plain text for a field's value. */
export function fieldValue(key: string, value: unknown): string {
  const f = FIELDS[key];
  if (value === null || value === undefined || value === "") return "none";
  return f?.fmt ? f.fmt(value) : show(value);
}

export const isInternalField = (key: string): boolean => FIELDS[key]?.internal === true || key.endsWith("_source_url");

/** Friendly names for each tool the run used (the table "Where each number came from"). */
export const TOOL_LABELS: Record<string, string> = {
  get_building_profile: "What you entered",
  lookup_ny_building_records: "City tax-lot, building-outline and energy records",
  get_solar_production: "Solar output estimate (NREL PVWatts)",
  get_utility_rates: "Electricity prices (U.S. Energy Information Administration)",
  get_utility_tariff: "Utility rate schedules (OpenEI)",
  search_ny_incentives_and_rules: "Incentives and rules (official pages)",
  get_hazard_context: "Flood zone (FEMA)",
  optimize_solar_storage: "Battery size (from your backup needs)",
  calculate: "Roof and solar math",
  run_financial_model: "Cost and savings model",
};
export const toolLabel = (tool: string): string => TOOL_LABELS[tool] ?? tidyKey(tool);

/**
 * A safety net for report text written before the plain-language rules (and for any slip after them): removes flag
 * prefixes and internal ids, turns code-style names into words, and swaps "placeholder" wording for "planning estimate".
 * The developer view shows the original text instead.
 */
export function plainify(text: string): string {
  return text
    .replace(/^\s*A\d{1,2}\s*[:\-.]\s*/, "")
    .replace(/^\s*Flag [a-z0-9_:]+:\s*/i, "")
    .replace(/\s*\(\s*(?:A\d{1,2}|C[1-4]|F-[ABC])(?:\s*(?:,|\/|and|&)\s*(?:A\d{1,2}|C[1-4]|F-[ABC]))*\s*\)/g, "")
    .replace(/,?\s*\bassumptions?\s+(?:A\d{1,2}|C[1-4]|F-[ABC])(?:\s*(?:,|and|&)\s*(?:A\d{1,2}|C[1-4]|F-[ABC]))*/gi, "")
    .replace(/,\s*(?:A\d{1,2}|C[1-4]|F-[ABC])(?=\s*\))/g, "")
    .replace(/\b(?:the|this|that)\s+(?:A\d{1,2}|C[1-4]|F-[ABC])\s+/gi, (m) => m.split(/\s+/)[0] + " ")
    .replace(/\b(?:see|and|in|from|on)\s+(?:A\d{1,2}|C[1-4]|F-[ABC])(?:\s*(?:,|and|\/)\s*(?:A\d{1,2}|C[1-4]|F-[ABC]))*\b/gi, "")
    .replace(/\s+(?:A\d{1,2}|C[1-4]|F-[ABC])\b/g, "")
    .replace(/(?<![/\-\w]|\w\.)[a-z]{2,}(?:_[a-z0-9]+)+(?![/\-\w]|\.\w)/g, (m) => m.replace(/_/g, " "))
    .replace(/\bteam planning (?:placeholder|figure)s?\b/gi, "planning estimate")
    .replace(/\bteam placeholders?\b/gi, (m) => (/s$/i.test(m) ? "planning estimates" : "planning estimate"))
    .replace(/\bplaceholders\b/gi, "planning estimates")
    .replace(/\bplaceholder\b/gi, "planning estimate")
    .replace(/25th\s*(?:-|to)\s*75th percentile/gi, "middle half")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([.,;:])/g, "$1")
    .replace(/,\s*([;.])/g, "$1")
    .trim();
}
