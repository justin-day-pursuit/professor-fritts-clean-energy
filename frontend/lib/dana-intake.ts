/**
 * Dana's fictional Queens library intake — same values as the backend case1 fixture.
 * Used when the user clicks "Load Dana's example" before the server stores the profile.
 */
import type { IntakeProfile } from "@/lib/types";

export const DANA_INTAKE: IntakeProfile = {
  contact_name: "Dana Reyes",
  building_name: "Queens Neighborhood Library Branch",
  address: "41-17 Main Street",
  borough: "Queens",
  city: "New York",
  state: "NY",
  building_type: "public library",
  floor_area_sqft: 18000,
  year_built: 1968,
  roof_type: "flat",
  roof_area_sqft: 6000,
  roof_replaced_year: 2019,
  utility: "Con Edison",
  annual_kwh: 310000,
  budget_amount: 400000,
  budget_year: 2026,
  budget_type: "capital",
  goal: "Cut grid electricity 30% by 2030",
  target_year: 2030,
  critical_loads: "Cooling center loads during outages",
  critical_load_hours: 8,
};

/** Default question Dana asks in the eval case and browser walkthrough. */
export const DANA_DEFAULT_QUESTION =
  "How can we cut grid power 30% by 2030 on $400k and stay open as a cooling center during outages?";
