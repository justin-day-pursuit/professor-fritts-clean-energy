"""
Real installed-cost range for solar, from NYSERDA's public project data (v7).

NYSERDA's "Solar Electric Programs Reported by NYSERDA" dataset lists every project it funded, with the
project cost and the nameplate size. This module takes the completed non-residential projects in the five
boroughs since 2022, groups them by size, and reports the 25th, 50th and 75th percentile cost per kW DC. That
replaces a guessed price with what comparable NYC projects actually cost. It is a cost of PAST projects, not a
quote: a bid for this roof replaces it.

A size band with too few projects returns None (the model then keeps its placeholder price and says so).
"""

from __future__ import annotations

import os
import time
from typing import Any

from tools.web import get_with_retry

NYSERDA_URL = "https://data.ny.gov/resource/3x8r-34rs.json"
NYSERDA_SOURCE_URL = "https://data.ny.gov/Energy-Environment/Solar-Electric-Programs-Reported-by-NYSERDA-Beginn/3x8r-34rs"
TIMEOUT_SECONDS = 30
NYC_COUNTIES = ("Bronx", "Kings", "New York", "Queens", "Richmond")
SINCE_DATE = "2022-01-01"
# Size bands in kW DC: (above, up to). Costs per kW fall as projects get bigger, so a roof is compared with its own band.
BANDS = ((25.0, 100.0), (100.0, 500.0), (500.0, 5000.0))
# Fewer comparable projects than this is not enough to quote a range.
MIN_PROJECTS = 20
CACHE_SECONDS = 24 * 3600

_cache: dict[tuple[float, float], tuple[float, dict[str, Any] | None]] = {}


class SolarCostError(RuntimeError):
    """The NYSERDA cost lookup failed; the model keeps its placeholder solar price."""


def band_for(kw: float) -> tuple[float, float]:
    """The size band a solar array of this many kW DC belongs in (arrays under 25 kW use the smallest band)."""
    for low, high in BANDS:
        if kw <= high:
            return (low, high)
    return BANDS[-1]


def cost_percentiles(rows: list[dict[str, Any]], band: tuple[float, float]) -> dict[str, Any] | None:
    """
    Cost per kW (25th, 50th, 75th percentile) for the projects in one size band, or None when too few.

    Rows with no cost or a zero cost are skipped; the cost per kW is project_cost divided by nameplate kW DC.
    """
    values = []
    for row in rows:
        try:
            cost, kw = float(row["project_cost"]), float(row["totalnameplatekwdc"])
        except (KeyError, TypeError, ValueError):
            continue
        if cost > 0 and band[0] < kw <= band[1]:
            values.append(cost / kw)
    if len(values) < MIN_PROJECTS:
        return None
    values.sort()
    n = len(values)

    def pick(q: float) -> float:
        return round(values[min(n - 1, int(n * q))])

    return {"p25_usd_per_kw": pick(0.25), "p50_usd_per_kw": pick(0.50), "p75_usd_per_kw": pick(0.75), "projects": n, "band_kw": list(band)}


def fetch_solar_cost_range(kw: float) -> dict[str, Any] | None:
    """Real NYC cost per kW DC for arrays of this size, from NYSERDA project data; cached for a day per band."""
    band = band_for(kw)
    cached = _cache.get(band)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return cached[1]
    counties = ",".join(f"'{c}'" for c in NYC_COUNTIES)
    params = {
        "$select": "project_cost,totalnameplatekwdc",
        "$where": (
            f"county in({counties}) AND sector='Non-Residential' AND project_status='Complete' "
            f"AND totalnameplatekwdc>{band[0]} AND totalnameplatekwdc<={band[1]} AND date_install>'{SINCE_DATE}'"
        ),
        "$limit": 5000,
    }
    headers = {"X-App-Token": os.environ["SODA_APP_TOKEN"].strip()} if os.environ.get("SODA_APP_TOKEN", "").strip() else {}
    try:
        response = get_with_retry(NYSERDA_URL, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise SolarCostError(f"NYSERDA data error (HTTP {response.status_code}).")
        rows = list(response.json())
    except SolarCostError:
        raise
    except Exception as exc:
        raise SolarCostError(f"NYSERDA cost request failed: {exc}") from exc
    result = cost_percentiles(rows, band)
    if result:
        result["since"] = SINCE_DATE
        result["source_url"] = NYSERDA_SOURCE_URL
    _cache[band] = (time.time(), result)
    return result


# ---- battery storage: NYSERDA's energy-storage incentive data (same idea as the solar prices above) ----

STORAGE_URL = "https://data.ny.gov/resource/ugya-enpy.json"
STORAGE_SOURCE_URL = "https://data.ny.gov/Energy-Environment/Residential-Retail-and-Bulk-Energy-Storage-Incentive/ugya-enpy"
_storage_cache: tuple[float, dict[str, Any] | None] | None = None


def storage_percentiles(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Cost per kWh (25th, 50th, 75th percentile) of NYC retail (commercial-scale) storage projects, or None when too few.

    Each project's cost per kWh is its total project cost divided by its installed energy capacity (kWh AC).
    Projects with no cost or no capacity are skipped.
    """
    values = []
    for row in rows:
        try:
            cost, kwh = float(row["total_project_cost"]), float(row["installed_energy_storage_kwhac"])
        except (KeyError, TypeError, ValueError):
            continue
        if cost > 0 and kwh > 0:
            values.append(cost / kwh)
    if len(values) < MIN_PROJECTS:
        return None
    values.sort()
    n = len(values)

    def pick(q: float) -> float:
        return round(values[min(n - 1, int(n * q))])

    return {"p25_usd_per_kwh": pick(0.25), "p50_usd_per_kwh": pick(0.50), "p75_usd_per_kwh": pick(0.75), "projects": n}


def fetch_storage_cost_range() -> dict[str, Any] | None:
    """Real NYC cost per kWh of battery projects from NYSERDA's retail storage data; cached for a day."""
    global _storage_cache
    if _storage_cache and time.time() - _storage_cache[0] < CACHE_SECONDS:
        return _storage_cache[1]
    counties = ",".join(f"'{c}'" for c in NYC_COUNTIES)
    params = {
        "$select": "total_project_cost,installed_energy_storage_kwhac",
        "$where": (
            f"program_type='Retail Storage' AND county in({counties}) AND project_status in('Completed','Approved') "
            "AND total_project_cost>0 AND installed_energy_storage_kwhac>0"
        ),
        "$limit": 5000,
    }
    headers = {"X-App-Token": os.environ["SODA_APP_TOKEN"].strip()} if os.environ.get("SODA_APP_TOKEN", "").strip() else {}
    try:
        response = get_with_retry(STORAGE_URL, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise SolarCostError(f"NYSERDA storage data error (HTTP {response.status_code}).")
        rows = list(response.json())
    except SolarCostError:
        raise
    except Exception as exc:
        raise SolarCostError(f"NYSERDA storage cost request failed: {exc}") from exc
    result = storage_percentiles(rows)
    if result:
        result["source_url"] = STORAGE_SOURCE_URL
    _storage_cache = (time.time(), result)
    return result
