"""
City energy records for one tax lot, from two NYC Open Data datasets keyed by BBL (v7).

  LL84  Local Law 84 energy benchmarking: the building's reported energy use each year (electricity in kWh,
        gas, oil, steam), its energy use per square foot (EUI) and its ENERGY STAR score.
  LL24  Local Law 24 solar readiness: the agency's own assessment of the roof (condition, age, whether it is
        solar ready) and any solar already installed or planned.

Both are real public records, so they replace guesses: a measured annual kWh instead of a benchmark, and the
city's own word on the roof. A building that is not in a dataset simply returns None; a failed lookup raises
CityEnergyError, which the records tool catches so the rest of the lookup still works.
"""

from __future__ import annotations

import os
from typing import Any

from tools.web import get_with_retry

LL84_URL = "https://data.cityofnewyork.us/resource/5zyy-y8am.json"
LL84_SOURCE_URL = "https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-Local-Law-84/5zyy-y8am"
LL24_URL = "https://data.cityofnewyork.us/resource/cfz5-6fvh.json"
LL24_SOURCE_URL = "https://data.cityofnewyork.us/City-Government/Solar-Readiness-Assessments-Local-Law-24/cfz5-6fvh"
TIMEOUT_SECONDS = 20


class CityEnergyError(RuntimeError):
    """A city energy-records lookup failed; the plan then has no city record for that part."""


def _headers() -> dict[str, str]:
    """The Socrata app token, when one is set, raises the rate limit."""
    token = os.environ.get("SODA_APP_TOKEN", "").strip()
    return {"X-App-Token": token} if token else {}


def _number(value: Any) -> float | None:
    """The datasets send numbers as text, with 'Not Available' or blanks for gaps and commas in some fields."""
    try:
        return float(str(value).replace(",", "").split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def _rows(url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    """One query against a dataset; any failure becomes CityEnergyError."""
    try:
        response = get_with_retry(url, params=params, headers=_headers(), timeout=TIMEOUT_SECONDS)
    except Exception as exc:  # network errors, timeouts
        raise CityEnergyError(f"NYC Open Data request failed: {exc}") from exc
    if response.status_code != 200:
        raise CityEnergyError(f"NYC Open Data error (HTTP {response.status_code}).")
    try:
        return list(response.json())
    except ValueError as exc:
        raise CityEnergyError("NYC Open Data sent an unreadable answer.") from exc


def parse_ll84_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    Pick the useful LL84 fields from one report row.

    electricity_use_grid_purchase is in kBtu and its "_1" twin is the same number in kWh, so the kWh
    column is used as is. A gap ("Not Available") becomes None, never 0.
    """
    return {
        "report_year": int(_number(row.get("report_year")) or 0) or None,
        "property_name": row.get("property_name"),
        "property_type": row.get("primary_property_type"),
        "gross_floor_area_sqft": _number(row.get("largest_property_use_type_1")),
        "site_eui_kbtu_per_sqft": _number(row.get("site_eui_kbtu_ft")),
        "weather_normalized_site_eui": _number(row.get("weather_normalized_site_eui")),
        "energy_star_score": _number(row.get("energy_star_score")),
        "electricity_kwh": _number(row.get("electricity_use_grid_purchase_1")),
        "natural_gas_kbtu": _number(row.get("natural_gas_use_kbtu")),
        "fuel_oil_kbtu": _number(row.get("fuel_oil_2_use_kbtu")),
        "district_steam_kbtu": _number(row.get("district_steam_use_kbtu")),
        "year_built": int(_number(row.get("year_built")) or 0) or None,
    }


def fetch_ll84(bbl: str) -> dict[str, Any] | None:
    """The newest LL84 energy report for the lot, or None when the building is not in the dataset."""
    rows = _rows(
        LL84_URL,
        {"$where": f"nyc_borough_block_and_lot='{int(bbl)}'", "$order": "report_year DESC", "$limit": 1},
    )
    return parse_ll84_row(rows[0]) if rows else None


def parse_ll24_row(row: dict[str, Any]) -> dict[str, Any]:
    """Pick the useful LL24 solar-readiness fields from one assessment row (text kept as the city wrote it)."""
    return {
        "agency": row.get("agency"),
        "site": row.get("site"),
        "status": row.get("status"),
        "solar_ready": str(row.get("solar_readiness_assessment") or "").strip().lower() == "yes",
        "roof_condition": row.get("roof_condition"),
        "roof_age": row.get("roof_age"),
        "report_year": int(_number(row.get("year_of_report")) or 0) or None,
        "installed_kw": _number(row.get("installed_or_estimated")),
        "estimated_annual_production_kwh": _number(row.get("estimated_annual_production")),
        "upfront_project_cost_usd": _number(str(row.get("upfront_project_cost") or "").replace("$", "")),
        "financing_mechanism": row.get("financing_mechanism"),
        "city_council_district": row.get("city_council_district"),
    }


def fetch_ll24(bbl: str) -> dict[str, Any] | None:
    """The newest LL24 assessment for the lot, or None when the building is not in the dataset."""
    rows = _rows(LL24_URL, {"bbl": str(int(bbl)), "$order": "year_of_report DESC", "$limit": 1})
    return parse_ll24_row(rows[0]) if rows else None
