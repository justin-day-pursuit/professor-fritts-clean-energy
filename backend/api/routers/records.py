"""
Public-records helpers for the intake form (v6).

GET /api/roof-suggestion looks up the building outlines on the lot at an address so the form can
suggest a roof area. It is a form helper, not an agent tool, and it works in any TOOL_MODE because it
only reads a free public dataset when the user clicks the button. The number is a suggestion that the
user must confirm, never a value the planner uses on its own.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from api import schemas
from tools.footprints import FootprintError, suggest_roof_area
from tools.geocode import GeocodeError

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
