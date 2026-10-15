"""
Live New York commercial electricity price from the EIA (v1).

Used by get_utility_rates when TOOL_MODE=live. This is a statewide average, not the building's
own tariff; the utility-specific tariff comes later from OpenEI.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from tools.base import ToolResult
from tools.web import get_with_retry

EIA_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"
EIA_SOURCE_URL = "https://www.eia.gov/electricity/data/browser/"

TIMEOUT_SECONDS = 15
MONTHS_AVERAGED = 12


class LiveRatesError(RuntimeError):
    """A live electricity price lookup failed in a way the agent should not paper over."""


def fetch_live_utility_rates(profile: dict[str, Any]) -> ToolResult:
    """Return the New York commercial electricity price: latest month and the 12-month average."""
    api_key = os.environ.get("EIA_API_KEY", "").strip()
    if not api_key:
        raise LiveRatesError("EIA_API_KEY is not set; add it to .env to use live electricity prices.")

    params = {
        "api_key": api_key,
        "frequency": "monthly",
        "data[0]": "price",
        "facets[stateid][]": "NY",
        "facets[sectorid][]": "COM",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": MONTHS_AVERAGED,
    }
    response = get_with_retry(EIA_URL, params=params, timeout=TIMEOUT_SECONDS)
    if response.status_code != 200:
        # Never echo the request URL: it carries the API key.
        raise LiveRatesError(f"EIA error (HTTP {response.status_code}).")
    # A partial series can contain months with no price yet; those cannot be averaged.
    rows = [row for row in response.json().get("response", {}).get("data", []) if row.get("price") is not None]
    if len(rows) < MONTHS_AVERAGED:
        raise LiveRatesError(f"EIA returned {len(rows)} months with a price; expected {MONTHS_AVERAGED}.")

    # EIA sends prices as text in cents per kWh. The average is the figure for annual savings (summer months
    # cost more); the lowest and highest month bound the dollar range.
    cents = [float(row["price"]) for row in rows]
    average_cents = sum(cents) / len(cents)

    return ToolResult(
        tool="get_utility_rates",
        data={
            "utility": profile.get("utility"),
            "tariff_name": "EIA New York commercial average (not the building's own tariff)",
            "avg_energy_charge_usd_per_kwh": round(average_cents / 100, 5),
            "price_low_usd_per_kwh": round(min(cents) / 100, 5),
            "price_high_usd_per_kwh": round(max(cents) / 100, 5),
            "latest_month_usd_per_kwh": round(cents[0] / 100, 5),
            "latest_month": rows[0]["period"],
            "months_averaged": len(rows),
            "period_start": rows[-1]["period"],
            "effective_date": rows[0]["period"],
            "price_units": rows[0]["price-units"],
        },
        source_url=EIA_SOURCE_URL,
        retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dataset_version=f"eia-retail-sales-{rows[0]['period']}",
        mock=False,
        flags=["statewide_average_rate"],
    )
