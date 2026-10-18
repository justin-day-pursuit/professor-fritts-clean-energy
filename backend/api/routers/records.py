"""
Public-records helpers for the intake form (v6).

GET /api/records/building-prefill asks the free city datasets what they already know about a building (yearly
electricity, the roof assessment, solar already installed, a roof-area suggestion) so the design page can fill in the form
before the visitor types anything. It uses no Claude and works in any TOOL_MODE. Every value is a suggestion the visitor confirms.

GET /api/roof-suggestion looks up the building outlines on the lot at an address so the form can
suggest a roof area. It is a form helper, not an agent tool, and it works in any TOOL_MODE because it
only reads a free public dataset when the user clicks the button. The number is a suggestion that the
user must confirm, never a value the planner uses on its own.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from api import schemas
from tools.city_energy import CityEnergyError, fetch_ll24, fetch_ll84
from tools.footprints import FootprintError, suggest_roof_area
from tools.geocode import GeocodeError
from tools.prefill import build_prefill

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/roof-suggestion", response_model=schemas.RoofSuggestionResponse)
def roof_suggestion(
    address: str = Query(..., min_length=3),
    borough: str | None = Query(default=None),
):
    """
    Suggest a roof area from NYC building footprints, with the buildings that were added up.

    A plain `def` on purpose: the lookup makes blocking web calls, and FastAPI runs it in a worker thread.
    Returns 404 with a readable sentence when the address or its outlines cannot be found, and 502 when
    the public service is down; in both cases the form tells the user to type the roof area themselves.
    """
    try:
        result = suggest_roof_area(address, borough)
    except (GeocodeError, FootprintError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="NYC Open Data is not answering right now. Type the roof area instead.") from exc
    return schemas.RoofSuggestionResponse(**result)


@router.get("/building-prefill", response_model=schemas.BuildingPrefillResponse)
def building_prefill(
    bbl: str = Query(..., min_length=10, max_length=10, pattern=r"^\d{10}$"),
    address: str = Query(..., min_length=3),
    borough: str | None = Query(default=None),
):
    """
    What the city's free records say about this tax lot, as values for the form.

    The lot number (BBL) comes from the address search the page already did. The three lookups are independent: if
    one fails or has nothing for the lot, the others still answer and `missing` says in plain words what is blank.
    A plain `def` on purpose, because the lookups make blocking web calls (FastAPI runs it in a worker thread).
    """
    problems: dict[str, str] = {}
    ll84 = ll24 = roof = None
    try:
        ll84 = fetch_ll84(bbl)
    except (CityEnergyError, httpx.HTTPError, ValueError):
        problems["energy"] = "unreachable"
    try:
        ll24 = fetch_ll24(bbl)
    except (CityEnergyError, httpx.HTTPError, ValueError):
        problems["roof_assessment"] = "unreachable"
    try:
        roof = suggest_roof_area(address, borough)
    except (GeocodeError, FootprintError):
        roof = None  # the city has nothing for this address
    except (httpx.HTTPError, ValueError):
        problems["roof_area"] = "unreachable"
    return schemas.BuildingPrefillResponse(**build_prefill(bbl, ll84, ll24, roof, problems))
