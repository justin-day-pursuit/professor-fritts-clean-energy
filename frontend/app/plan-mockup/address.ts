/**
 * Looking up a New York City address and its building, straight from the visitor's browser.
 *
 * Two free public city services are used, and neither needs a key or uses any Claude credits:
 *  - NYC Planning's address search (GeoSearch), which only knows New York City, so "no match" is how a Boston or Albany
 *    address shows up,
 *  - the city's tax-lot file (PLUTO) on NYC Open Data, which lists who owns the lot, what it is used for and how big it is.
 * The owner on that file is how the page tells a public building from a private one.
 */

const SEARCH_URL = "https://geosearch.planninglabs.nyc/v2/autocomplete";
const PLUTO_URL = "https://data.cityofnewyork.us/resource/64uk-42ks.json";

/** One address offered in the list as the visitor types. */
export interface AddressSuggestion {
  label: string;
  borough: string;
  /** The tax lot number the city uses to find the building exactly. */
  bbl: string;
}

/** What the city's tax-lot file says about one lot. Every field can be missing. */
export interface BuildingRecord {
  address?: string;
  borough?: string;
  bbl?: string;
  ownertype?: string;
  ownername?: string;
  landuse?: string;
  bldgclass?: string;
  yearbuilt?: string;
  bldgarea?: string;
  numfloors?: string;
  zipcode?: string;
}

/** Addresses that match what has been typed so far. An empty list means the city has no such address. */
export async function suggestAddresses(text: string, signal: AbortSignal): Promise<AddressSuggestion[]> {
  const url = `${SEARCH_URL}?text=${encodeURIComponent(text)}&size=8`;
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`Address search answered ${response.status}`);
  const body = (await response.json()) as { features?: { properties?: Record<string, unknown> }[] };
  const seen = new Set<string>();
  const out: AddressSuggestion[] = [];
  for (const f of body.features ?? []) {
    const p = f.properties ?? {};
    const bbl = (p.addendum as { pad?: { bbl?: string } } | undefined)?.pad?.bbl;
    const label = typeof p.label === "string" ? p.label.replace(/, NY, USA$/, "") : "";
    if (!bbl || !label || seen.has(label)) continue;
    seen.add(label);
    out.push({ label, borough: typeof p.borough === "string" ? p.borough : "", bbl });
  }
  return out;
}

/** The tax-lot record for one lot, or null when the file has nothing for it (a condo lot, for example). */
export async function fetchBuildingRecord(bbl: string): Promise<BuildingRecord | null> {
  const fields = "address,borough,bbl,ownertype,ownername,landuse,bldgclass,yearbuilt,bldgarea,numfloors,zipcode";
  const url = `${PLUTO_URL}?bbl=${encodeURIComponent(bbl)}&$select=${fields}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Tax-lot lookup answered ${response.status}`);
  const rows = (await response.json()) as BuildingRecord[];
  return rows[0] ?? null;
}

/** Whether the lot looks like a public building, a private one, or cannot be told from the owner on the file. */
export type OwnerKind = "public" | "unclear" | "private";

/**
 * Reads the owner type on the tax-lot file: C is the City, O is another public owner (a state or federal agency, a public
 * authority) and S is the State, so those count as public. M is mixed City and private ownership and X is a fully
 * tax-exempt lot, which can be public or a private institution, so those are "unclear" and the visitor is asked.
 * Anything else, including no owner type, is treated as private.
 */
export function ownerKind(record: BuildingRecord | null): OwnerKind {
  if (!record) return "unclear";
  const type = (record.ownertype ?? "").trim().toUpperCase();
  if (type === "C" || type === "O" || type === "S") return "public";
  if (type === "M" || type === "X") return "unclear";
  return "private";
}

const LAND_USE: Record<string, string> = {
  "01": "One and two family home",
  "02": "Walk-up apartment building",
  "03": "Elevator apartment building",
  "04": "Mixed residential and commercial building",
  "05": "Commercial or office building",
  "06": "Industrial or manufacturing building",
  "07": "Transportation or utility building",
  "08": "Public facility or institution",
  "09": "Open space or recreation",
  "10": "Parking",
  "11": "Vacant land",
};

/** The building's use in plain words, from its tax class and land use code. */
export function buildingTypeLabel(record: BuildingRecord | null): string {
  if (!record) return "Building";
  const cls = (record.bldgclass ?? "").toUpperCase();
  if (cls.startsWith("W")) return "School or educational building";
  if (cls.startsWith("I")) return "Hospital or health building";
  if (cls.startsWith("Y")) return "City services building";
  return LAND_USE[(record.landuse ?? "").padStart(2, "0")] ?? "Building";
}

/** A number from the file, or null when it is missing or not a number. */
export function numberOf(value: string | undefined): number | null {
  if (value === undefined) return null;
  const n = Number(value);
  return Number.isFinite(n) && n > 0 ? n : null;
}

/** Everything the page knows about the building the visitor chose. */
export interface FoundBuilding {
  label: string;
  borough: string;
  bbl: string;
  record: BuildingRecord | null;
  kind: OwnerKind;
  /** The visitor said to go ahead although the owner is not clearly public. */
  accepted: boolean;
}
