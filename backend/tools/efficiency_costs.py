"""
Real cost of efficiency work, from NYSERDA's "Energy Efficiency Completed Projects" data (v7).

The dataset (data.ny.gov erjw-j2zx) lists completed public-sector efficiency projects, mostly done through the New
York Power Authority, with each project's total cost and the electricity it saves each year. This module takes the
New York City projects since 2016 and reports the 25th, 50th and 75th percentile COST PER kWh SAVED PER YEAR:

  standard efficiency (LED lighting and controls)  <- projects in the "Energy Efficiency - LED Lighting" category
  deep efficiency (lighting plus HVAC, envelope)   <- projects in the "Energy Efficiency - Comprehensive" category

That replaces the old guessed dollars per square foot. It does NOT say how much a given building will save: the
dataset has no baseline use for each project, so the savings percent (10-20% standard, 15-25% deep) is still a team
placeholder. A project's cost may also cover savings in gas or oil that this dataset does not count in kWh, which
makes the cost per kWh look higher than it is for electricity alone.

A category with too few projects returns None and the model keeps its placeholder price per square foot.
"""

from __future__ import annotations

import os
import time
from typing import Any

from tools.web import get_with_retry

EFFICIENCY_URL = "https://data.ny.gov/resource/erjw-j2zx.json"
EFFICIENCY_SOURCE_URL = "https://data.ny.gov/Energy-Environment/Energy-Efficiency-Completed-Projects-Beginning-1987/erjw-j2zx"
TIMEOUT_SECONDS = 30
SINCE_YEAR = 2016
NYC_COUNTIES = ("BRONX", "KINGS", "NEW YORK", "QUEENS", "RICHMOND")
# Which dataset category stands for each efficiency level in the model.
CATEGORIES = {
    "standard": "Energy Efficiency - LED Lighting",
    "deep": "Energy Efficiency - Comprehensive",
}
MIN_PROJECTS = 20
CACHE_SECONDS = 24 * 3600

_cache: tuple[float, dict[str, Any] | None] | None = None


class EfficiencyCostError(RuntimeError):
    """The efficiency cost lookup failed; the model keeps its placeholder price per square foot."""


def cost_per_kwh_saved(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    25th, 50th and 75th percentile dollars per kWh saved per year, or None when fewer than MIN_PROJECTS qualify.

    A project counts only when its cost and its yearly kWh saved are both above zero.
    """
    values = []
    for row in rows:
        try:
            cost, kwh = float(row["total_project_cost"]), float(row["electric_energy_reduction_kwh"])
        except (KeyError, TypeError, ValueError):
            continue
        if cost > 0 and kwh > 0:
            values.append(cost / kwh)
    if len(values) < MIN_PROJECTS:
        return None
    values.sort()
    n = len(values)

    def pick(q: float) -> float:
        return round(values[min(n - 1, int(n * q))], 2)

    return {"p25": pick(0.25), "p50": pick(0.50), "p75": pick(0.75), "projects": n}


def fetch_efficiency_cost_ranges() -> dict[str, Any] | None:
    """
    {"standard": {...}, "deep": {...}, "since", "source_url"} from NYSERDA's data, cached for a day, or None when
    either level has too few projects.
    """
    global _cache
    if _cache and time.time() - _cache[0] < CACHE_SECONDS:
        return _cache[1]
    counties = ",".join(f"'{c}'" for c in NYC_COUNTIES)
    categories = ",".join(f"'{c}'" for c in CATEGORIES.values())
    params = {
        "$select": "project_category,total_project_cost,electric_energy_reduction_kwh",
        "$where": (
            f"year_completed>={SINCE_YEAR} AND ny_state_county in({counties}) AND project_category in({categories}) "
            "AND total_project_cost>0 AND electric_energy_reduction_kwh>0"
        ),
        "$limit": 5000,
    }
    headers = {"X-App-Token": os.environ["SODA_APP_TOKEN"].strip()} if os.environ.get("SODA_APP_TOKEN", "").strip() else {}
    try:
        response = get_with_retry(EFFICIENCY_URL, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise EfficiencyCostError(f"NYSERDA efficiency data error (HTTP {response.status_code}).")
        rows = list(response.json())
    except EfficiencyCostError:
        raise
    except Exception as exc:
        raise EfficiencyCostError(f"NYSERDA efficiency cost request failed: {exc}") from exc
    found: dict[str, Any] = {}
    for level, category in CATEGORIES.items():
        stats = cost_per_kwh_saved([r for r in rows if r.get("project_category") == category])
        if stats is None:
            _cache = (time.time(), None)
            return None
        found[level] = stats
    found["since"] = SINCE_YEAR
    found["source_url"] = EFFICIENCY_SOURCE_URL
    _cache = (time.time(), found)
    return found
