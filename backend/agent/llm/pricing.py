"""
What a Claude call costs, estimated from the token counts the API returns (v6).

The API reports four token counts on every reply: normal input, input written to the cache, input read
from the cache, and output. The app saves them with each run so spend can be seen without access to the
Anthropic console (the key belongs to the institution). The dollar figure is an ESTIMATE from the price
table below, which is why it is shown as "estimated_usd" and is None for a model that is not listed.

To add a model, add a row of dollars per million tokens: input, output, cache read, cache write.
Cache write is 1.25x the input price (the standard 5-minute cache write); that multiplier is an assumption
taken from Anthropic's published pricing pattern, not read from the API. Check the figures against
Anthropic's pricing page before relying on them. Last checked: Oct 15, 2026.
"""

from __future__ import annotations

from typing import Any

# (input, output, cache read, cache write) in USD per million tokens.
PRICES_USD_PER_MTOK: dict[str, tuple[float, float, float, float]] = {
    "claude-sonnet-5-5": (2.00, 10.00, 0.20, 2.50),
    "claude-opus-5-5": (4.00, 20.00, 0.20, 5.00),
}


def estimate_cost_usd(model: str, usage: dict[str, Any]) -> float | None:
    """
    Estimated dollars for one call (or the sum of several), or None when the model has no price here.

    usage uses the keys input_tokens, output_tokens, cache_creation_input_tokens and cache_read_input_tokens.
    Thinking tokens are already inside output_tokens, so they are priced as output.
    """
    prices = PRICES_USD_PER_MTOK.get(model)
    if prices is None:
        return None
    price_in, price_out, price_read, price_write = prices
    total = (
        usage.get("input_tokens", 0) * price_in
        + usage.get("output_tokens", 0) * price_out
        + usage.get("cache_read_input_tokens", 0) * price_read
        + usage.get("cache_creation_input_tokens", 0) * price_write
    ) / 1_000_000
    return round(total, 4)


def sum_usage(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Add up per-call usage records: token counts, call count, and the estimated dollars when every call has one."""
    keys = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    totals: dict[str, Any] = {key: sum(int(item.get(key, 0) or 0) for item in items) for key in keys}
    totals["calls"] = len(items)
    costs = [item.get("estimated_usd") for item in items]
    totals["estimated_usd"] = round(sum(costs), 4) if costs and all(c is not None for c in costs) else None
    models = sorted({str(item.get("model")) for item in items if item.get("model")})
    totals["models"] = models
    return totals
