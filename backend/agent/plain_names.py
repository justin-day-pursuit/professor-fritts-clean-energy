"""
Plain-language names for the things the code calls by short ids (v7).

The tools and notes label every calculation and assumption with an id (C1, F-B, A7). Those ids exist so a statement can be
traced back to its math, but a facilities manager should never have to read one. This module gives each id a plain name and a
plain-words formula, and strips the id prefix from assumption sentences, so the report and the screen can show words.
"""

from __future__ import annotations

import re

# What each calculation is, in the words a manager would use.
CALCULATION_NAMES = {
    "C1": "Usable roof area",
    "C2": "Solar array size",
    "C3": "Solar share of your electricity use",
    "C4": "Yearly bill savings from solar",
    "F-A": "Plan A costs and savings",
    "F-B": "Plan B costs and savings",
    "F-C": "Plan C costs and savings",
}
# The math behind each, in plain words (the code's own formula stays available for the developer view).
CALCULATION_FORMULAS = {
    "C1": "Roof area x the share that is usable after setbacks and equipment",
    "C2": "Usable roof area / roof area one kilowatt of panels needs",
    "C3": "Yearly solar output / yearly electricity use",
    "C4": "Yearly solar output x electricity price",
    "F-A": "Efficiency cost and savings, priced from similar NYC projects",
    "F-B": "Efficiency plus solar, within your budget",
    "F-C": "Deeper efficiency, solar on the whole roof, and a backup battery",
}

# The tools by what they do, for the sentences that say a lookup failed.
TOOL_NAMES = {
    "get_building_profile": "Reading your building details",
    "lookup_ny_building_records": "The city building-records lookup",
    "get_solar_production": "The solar output estimate",
    "get_utility_rates": "The electricity price lookup",
    "get_utility_tariff": "The utility rate-schedule lookup",
    "search_ny_incentives_and_rules": "The incentives and rules check",
    "get_hazard_context": "The flood-zone lookup",
    "optimize_solar_storage": "The battery sizing",
    "calculate": "The roof and solar math",
    "run_financial_model": "The cost and savings model",
}

_ID_PREFIX = re.compile(r"^\s*A\d{1,2}\s*[:\-.]\s*")


def calculation_name(calc_id: str) -> str:
    """The plain name for a calculation id; an id with no entry is returned as written."""
    return CALCULATION_NAMES.get(calc_id, calc_id)


def calculation_formula(calc_id: str) -> str | None:
    """The plain-words formula for a calculation id, or None."""
    return CALCULATION_FORMULAS.get(calc_id)


def tool_name(tool: str) -> str:
    """What a tool does, in plain words; an unknown tool is shown with its underscores turned into spaces."""
    return TOOL_NAMES.get(tool, tool.replace("_", " "))


def strip_id_prefix(text: str) -> str:
    """Remove a leading assumption id ("A7: ...") from a sentence, so the reader sees only the sentence."""
    return _ID_PREFIX.sub("", text, count=1)
