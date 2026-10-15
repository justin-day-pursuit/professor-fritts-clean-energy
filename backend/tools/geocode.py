"""
NYC address lookup shared by the live tools (v1) — the free NYC Planning Labs geocoder.

It understands boroughs, which the US Census geocoder does not ("Queens" finds nothing there).
"""

from __future__ import annotations

import re
from typing import Any

from tools.web import get_with_retry

GEOCODE_URL = "https://geosearch.planninglabs.nyc/v2/search"
TIMEOUT_SECONDS = 10


APPROXIMATE_BELOW_CONFIDENCE = 0.8


class GeocodeError(RuntimeError):
    """The address could not be placed on a New York City lot."""


def borough_of(profile: dict[str, Any]) -> str | None:
    """The borough from the intake; the form's "Borough or county" field may arrive as county."""
    return (profile.get("borough") or profile.get("county") or "").strip() or None


def _house_number_fits(address: str, label: str) -> bool:
    """
    Whether the geocoder's label starts with the same house number as the address.

    Hyphens and spaces are ignored ("89-11" and "8911" match). An address that does not start
    with a number, such as "Queens Central Library", has no house number to compare, so it passes
    and the confidence score decides whether it is flagged as approximate.
    """
    first = address.split()[0]
    if not first[0].isdigit():
        return True
    squash = lambda text: re.sub(r"[^0-9A-Za-z]", "", text)
    return squash(label.split()[0]) == squash(first) if label.split() else False


def geocode_nyc_address(address: str, borough: str | None) -> dict[str, Any]:
    """Turn a street address into coordinates and the tax lot ID (BBL)."""
    if not address or not address.strip():
        raise GeocodeError("No address to look up.")
    text = ", ".join(part for part in (address, borough, "NY") if part)
    response = get_with_retry(GEOCODE_URL, params={"text": text, "size": 1}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        raise GeocodeError(f"The NYC geocoder found no match for {text!r}.")
    props = features[0]["properties"]
    lon, lat = features[0]["geometry"]["coordinates"]
    if not _house_number_fits(address, str(props.get("label", ""))):
        raise GeocodeError(f"Geocoder matched {props.get('label')!r}, which does not fit {address!r}.")
    return {
        "label": props.get("label"),
        "borough": props.get("borough"),
        "postalcode": props.get("postalcode"),
        "match_type": props.get("match_type"),
        "confidence": props.get("confidence"),
        "bbl": (props.get("addendum") or {}).get("pad", {}).get("bbl"),
        "lat": lat,
        "lon": lon,
    }


def is_approximate(place: dict[str, Any]) -> bool:
    """True when the geocoder was not confident, so the matched lot may not be the building's own."""
    return (place.get("confidence") or 0) < APPROXIMATE_BELOW_CONFIDENCE
