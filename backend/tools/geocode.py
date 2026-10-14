"""
NYC address lookup shared by the live tools (v1) — the free NYC Planning Labs geocoder.

It understands boroughs, which the US Census geocoder does not ("Queens" finds nothing there).
"""

from __future__ import annotations

from typing import Any

from tools.web import get_with_retry

GEOCODE_URL = "https://geosearch.planninglabs.nyc/v2/search"
TIMEOUT_SECONDS = 30


APPROXIMATE_BELOW_CONFIDENCE = 0.8


class GeocodeError(RuntimeError):
    """The address could not be placed on a New York City lot."""


def geocode_nyc_address(address: str, borough: str | None) -> dict[str, Any]:
    """Turn a street address into coordinates and the tax lot ID (BBL)."""
    text = ", ".join(part for part in (address, borough, "NY") if part)
    response = get_with_retry(GEOCODE_URL, params={"text": text, "size": 1}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        raise GeocodeError(f"The NYC geocoder found no match for {text!r}.")
    props = features[0]["properties"]
    lon, lat = features[0]["geometry"]["coordinates"]
    street_number = address.split()[0]
    if not str(props.get("label", "")).startswith(street_number):
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
