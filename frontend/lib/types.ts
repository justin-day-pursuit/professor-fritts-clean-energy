/**
 * TypeScript shapes for API JSON — kept in sync with backend/api/schemas.py and agent/claims.py.
 * When the backend adds fields, update the matching interface here so the UI stays type-safe.
 */

export type JsonObject = Record<string, unknown>;

export interface HealthResponse {
  status: string;
  tool_mode: string;
  llm_provider: string;
  django_version: string;
}

export interface SessionCreateRequest {
  profile?: JsonObject;
  fixture_case?: string | null;
}

export interface ProfileUpdateRequest {
  profile: JsonObject;
}

export interface SessionResponse {
  id: string;
  created_at: string;
  profile: JsonObject;
  status: string;
  fixture_case: string;
}

export interface DocumentResponse {
  id: number;
  session_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  stored_path: string;
  parsed_summary: JsonObject;
  created_at: string;
}

export interface MessageResponse {
  id: number;
  session_id: string;
  role: string;
  content: string;
  created_at: string;
  run_id: number | null;
}

export interface RunEventResponse {
  id: number;
  seq: number;
  kind: string;
  payload: JsonObject;
  created_at: string;
}

export interface MessageCreateRequest {
  content: string;
}

export interface RunResponse {
  id: number;
  session_id: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  tool_mode: string;
  llm_provider: string;
  tool_call_count: number;
  elapsed_seconds: number | null;
  output: JsonObject;
  flags: JsonObject;
  created_at: string;
  events: RunEventResponse[];
}

export interface MessageRunResponse {
  message: MessageResponse | null;
  run: RunResponse;
}

/** One mock situation from GET /api/dev/fixtures. */
export interface FixtureSummary {
  id: string;
  building_name: string;
  goal: string;
  question: string;
}

export interface FixtureListResponse {
  fixtures: FixtureSummary[];
}

/** POST /api/dev/fixtures/{id}/run — the trace, including failed runs. */
export interface FixtureRunResponse {
  run: RunResponse;
}

/** Intake profile fields the left-hand form reads and writes. */
export interface IntakeProfile {
  address?: string;
  borough?: string;
  county?: string;
  city?: string;
  state?: string;
  building_type?: string;
  floor_area_sqft?: number | string;
  year_built?: number | string;
  roof_type?: string;
  roof_area_sqft?: number | string;
  roof_replaced_year?: number | string;
  utility?: string;
  annual_kwh?: number | string;
  budget_amount?: number | string;
  budget_year?: number | string;
  budget_type?: string;
  goal?: string;
  target_year?: number | string;
  critical_loads?: string;
  critical_load_hours?: number | string;
  /** Usable roof area (sq ft) an engineer or roofer verified. Needed before solar is sized on a roof that is not flat. */
  verified_usable_roof_sqft?: number | string;
  /** Solar already on the roof: size in kW DC and what it makes in a year. */
  existing_solar_kw?: number | string;
  existing_solar_kwh?: number | string;
  /** Free text: other renewables and efficiency work the building already has ("none" if none). */
  existing_renewables?: string;
  existing_efficiency?: string;
  contact_name?: string;
  building_name?: string;
}

export type ClaimLabel = "FACT" | "ESTIMATE" | "ASSUMPTION" | "RECOMMENDATION";
export type ClaimConfidence = "high" | "medium" | "low";

export interface Claim {
  text: string;
  label: ClaimLabel;
  confidence: ClaimConfidence;
  source_url?: string | null;
  calc_id?: string | null;
  assumption_id?: string | null;
}

export interface RoadmapSection {
  section_id: string;
  title: string;
  claims: Claim[];
  stand_in_note?: string | null;
}

export interface RoadmapPayload {
  sections: RoadmapSection[];
  footer_note?: string;
}

export interface ToolResultPayload {
  tool?: string;
  data?: JsonObject;
  source_url?: string;
  retrieved_at?: string;
  dataset_version?: string;
  mock?: boolean;
  stale?: boolean;
  flags?: string[];
}

/** One building outline on the tax lot, from NYC building footprints. */
export interface RoofBuilding {
  area_sqft: number;
  height_ft: number | null;
  construction_year: number | null;
  name: string | null;
  counted: boolean;
}

/** GET /api/records/roof-suggestion: a suggested roof area. It is not a measured roof. */
export interface RoofSuggestion {
  suggested_roof_area_sqft: number;
  total_footprint_sqft: number;
  largest_footprint_sqft: number;
  building_count: number;
  buildings: RoofBuilding[];
  bbl: string;
  geocoder_match: string | null;
  source_url: string;
  retrieved_at: string;
  note: string;
}
