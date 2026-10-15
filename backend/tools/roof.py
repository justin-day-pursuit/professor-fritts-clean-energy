"""
Roof type rules for solar sizing (v6).

The solar formulas assume a flat commercial roof: a setback factor of 0.55 of the roof area, 66 sq ft of
roof per kW, and PVWatts defaults of a 10 degree tilt facing south. A pitched roof, a tower, a dome or a
mixed roof does not follow any of that, so the planner never sizes one from those flat-roof numbers.
Instead it tells the user to have an engineer or roofer verify the usable roof area. Once they type that
number into the intake (verified_usable_roof_sqft), the array is sized from it.

Add a word to NON_FLAT_WORDS to make another description count as not flat.
"""

from __future__ import annotations

import re
from typing import Any

from tools.base import ToolUnavailableError

# Words in the roof type that mean the roof is not a plain flat roof. Checked before the flat words,
# so "flat roof with a clock tower" counts as not flat.
NON_FLAT_WORDS = (
    "pitch", "slope", "sloped", "gable", "hip", "mansard", "dome", "tower", "steep", "barrel",
    "vault", "spire", "cupola", "shingle", "slate", "mixed", "other",
)

VERIFY_MESSAGE = (
    "The roof is {kind}, so the usable area and array size cannot be estimated from the flat-roof defaults. "
    "Ask the user to have an engineer or a roofer verify the usable roof area, and to enter it as "
    "'verified_usable_roof_sqft' in the intake. Do not size solar for this roof until then; say so in the plan."
)


class RoofNotSizableError(ToolUnavailableError):
    """Solar cannot be sized for this roof yet: it is not flat and no verified usable area was given."""


def roof_kind(roof_type: Any) -> str:
    """
    "flat", "non_flat" or "unknown" for the roof type text from the intake.

    Blank, "unknown" and anything with no flat or non-flat word is "unknown", which keeps the flat-roof
    behavior (the intake flags a missing roof type separately so the plan lowers its confidence).
    """
    text = str(roof_type or "").strip().lower()
    if not text or text in ("unknown", "not sure"):
        return "unknown"
    # "low-slope" is a flat roof, so it is taken out before the "slope" word is looked for.
    without_low_slope = re.sub(r"low[-_ ]slope", " ", text)
    if any(re.search(r"\b" + word, without_low_slope) for word in NON_FLAT_WORDS):
        return "non_flat"
    if "flat" in text or "low-slope" in text or "low slope" in text or "low_slope" in text:
        return "flat"
    return "unknown"


def verified_usable_area(profile: dict[str, Any]) -> float | None:
    """The usable roof area an engineer or roofer verified, or None when the intake has none above zero."""
    try:
        value = float(profile.get("verified_usable_roof_sqft"))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def check_roof_sizing_allowed(profile: dict[str, Any]) -> None:
    """Raise RoofNotSizableError when the roof is not flat and its usable area was not verified."""
    if roof_kind(profile.get("roof_type")) == "non_flat" and verified_usable_area(profile) is None:
        raise RoofNotSizableError(VERIFY_MESSAGE.format(kind=f"not flat ({profile.get('roof_type')!r})"))


# The shared flat-roof sizing defaults (formulas C1 and C2). Kept here so every tool agrees.
SETBACK_FACTOR = 0.55
SQFT_PER_KW = 66.0
# An array a few percent over the free roof is rounding, not a mistake.
ARRAY_TOLERANCE = 1.05


def number_from_profile(profile: dict[str, Any], key: str) -> float | None:
    """A positive number from the intake profile, or None when it is blank, text or not above zero."""
    try:
        value = float(profile.get(key))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def usable_array_kw(profile: dict[str, Any]) -> float | None:
    """
    Whole-roof array size in kW DC from the intake, before any existing array is taken out.

    A verified usable area (from an engineer or roofer) is used as it is. Otherwise the roof area is cut
    by the setback factor, as in formula C1, and divided by the roof area per kW, as in C2.
    Returns None when the intake has no roof area to work from.
    """
    verified = verified_usable_area(profile)
    if verified is not None:
        return verified / SQFT_PER_KW
    roof = number_from_profile(profile, "roof_area_sqft")
    return roof * SETBACK_FACTOR / SQFT_PER_KW if roof else None


def existing_solar_kw(profile: dict[str, Any]) -> float:
    """Size of the solar array already on the roof, in kW DC (0 when the intake lists none)."""
    return number_from_profile(profile, "existing_solar_kw") or 0.0


def free_array_kw(profile: dict[str, Any]) -> float | None:
    """Room left for a NEW array: the whole-roof size minus the existing array, never below zero."""
    whole = usable_array_kw(profile)
    if whole is None:
        return None
    return max(0.0, whole - existing_solar_kw(profile))


def check_new_array_fits(profile: dict[str, Any], system_kw: float | None) -> None:
    """
    Refuse a new array that does not fit beside the existing one (v6).

    With no existing solar this does nothing. With existing solar, a roof that is already full raises
    RoofNotSizableError, and a requested size above the free capacity raises a ValueError that names the
    largest size that fits, so the model can try again.
    """
    existing = existing_solar_kw(profile)
    free = free_array_kw(profile)
    if existing <= 0 or free is None:
        return
    whole = usable_array_kw(profile) or 0.0
    if free <= 0:
        raise RoofNotSizableError(
            f"The existing {existing:.0f} kW array already uses the whole usable roof (about {whole:.0f} kW "
            "estimated). There is no free roof for a new array; plan efficiency and say so."
        )
    if system_kw is not None and system_kw > free * ARRAY_TOLERANCE:
        raise ValueError(
            f"A {system_kw:.0f} kW array does not fit beside the existing {existing:.0f} kW array. "
            f"The free roof holds about {free:.0f} kW; send system_kw of {free:.0f} or less."
        )
