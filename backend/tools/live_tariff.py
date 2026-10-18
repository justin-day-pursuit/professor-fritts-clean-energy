"""
Live utility tariff candidates from OpenEI's Utility Rate Database (v7).

Which tariff a building is on depends on its peak demand, voltage and meter, none of which the intake asks for, and
a tariff's real price depends on demand charges, time-of-day periods and riders. A single price per kWh pulled from
the database would look precise and be wrong. So this tool returns what is real and checkable: the CURRENT general
service tariffs the utility publishes for New York City (name, effective date, fixed monthly charge and the OpenEI
page), flagged so the plan says the building's own tariff must be confirmed on a bill. No energy price comes from
here; the savings use the EIA state average, as before.

Needs the free OPENEI_API_KEY. Without it, or when OpenEI has nothing for the utility, the tool reports itself
unavailable instead of falling back to sample data.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from tools.base import ToolResult, ToolUnavailableError
from tools.web import get_with_retry

OPENEI_URL = "https://api.openei.org/utility_rates"
OPENEI_SOURCE_URL = "https://openei.org/wiki/Utility_Rate_Database"
OPENEI_RATE_PAGE = "https://apps.openei.org/USURDB/rate/view/"
TIMEOUT_SECONDS = 40
MAX_CANDIDATES = 8

# The name OpenEI uses for each utility the planner knows; other names are tried as typed.
UTILITY_NAMES = {
    "con edison": "Consolidated Edison Co-NY Inc",
    "coned": "Consolidated Edison Co-NY Inc",
    "consolidated edison": "Consolidated Edison Co-NY Inc",
}
# General-service tariffs a commercial or public building is normally on, without the zone-specific copies.
GENERAL_SERVICE = re.compile(r"^SC[- ]?(2|9)\b.*General (Small|Large)", re.I)


def pick_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    The current general-service tariffs for New York City, newest first, at most MAX_CANDIDATES.

    "Current" means no end date. Zone-specific copies and other regions (Westchester) are left out.
    """
    chosen = []
    for item in items:
        name = str(item.get("name") or "")
        if item.get("enddate") or "[NYC]" not in name or "Zone" in name or not GENERAL_SERVICE.search(name):
            continue
        started = item.get("startdate")
        fixed = item.get("fixedchargefirstmeter")
        chosen.append({
            "tariff_name": name,
            "effective_date": datetime.fromtimestamp(started, timezone.utc).strftime("%Y-%m-%d") if started else None,
            "fixed_charge_usd_per_month": fixed if str(item.get("fixedchargeunits") or "").endswith("month") else None,
            "openei_url": OPENEI_RATE_PAGE + str(item.get("label")),
        })
    chosen.sort(key=lambda c: c["effective_date"] or "", reverse=True)
    return chosen[:MAX_CANDIDATES]


def fetch_live_tariff(profile: dict[str, Any]) -> ToolResult:
    """Current general-service tariff candidates for the building's utility, from OpenEI."""
    key = os.environ.get("OPENEI_API_KEY", "").strip()
    if not key:
        raise ToolUnavailableError("No OPENEI_API_KEY is set, so tariffs cannot be looked up.")
    typed = str(profile.get("utility") or "Con Edison").strip()
    utility = UTILITY_NAMES.get(typed.lower(), typed)
    params = {
        "version": "8", "format": "json", "api_key": key, "ratesforutility": utility,
        "sector": "Commercial", "approved": "true", "limit": "500", "detail": "full",
    }
    try:
        response = get_with_retry(OPENEI_URL, params=params, timeout=TIMEOUT_SECONDS)
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ToolUnavailableError(f"OpenEI tariff request failed: {exc}") from exc
    if response.status_code != 200 or body.get("errors"):
        raise ToolUnavailableError(f"OpenEI returned no usable answer ({body.get('errors') or response.status_code}).")
    candidates = pick_candidates(body.get("items") or [])
    if not candidates:
        raise ToolUnavailableError(f"OpenEI lists no current general-service New York City tariffs for {utility!r}.")
    return ToolResult(
        tool="get_utility_tariff",
        data={
            "utility": utility,
            "candidate_tariffs": candidates,
            "note": (
                "These are the current general-service tariffs the utility publishes for New York City. Which one "
                "applies depends on peak demand, voltage and meter, so the building's own tariff is not chosen here and "
                "no energy price is taken from this list. Savings use the EIA state average instead."
            ),
            "needs_user_confirmation": True,
        },
        source_url=OPENEI_SOURCE_URL,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version="openei-usrdb-v8",
        mock=False,
        flags=["tariff_needs_user_confirmation"],
    )
