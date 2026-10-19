"""
Replay saved demos in the planner (v6).

POST /api/replay/{case} plays a saved run back through our real harness: the scripted model replays the saved
steps, the tools read their saved answers, and all four checks run. It never calls Claude and never calls a live
tool, whatever the server is set to, so the button is safe to leave on the public site. It only accepts the cases
listed in REPLAY_CASES, so it cannot be pointed at anything else. Each replay adds a small session and run to the
database like any other run.
"""

from __future__ import annotations

from asgiref.sync import sync_to_async
from fastapi import APIRouter, HTTPException

from agent.harness import run_harness
from api import schemas
from core import services
from core.models import Message
from mocks.catalog import FIXTURES_ROOT, load_case
from mocks.mock_mode import forced_tool_mode

router = APIRouter(prefix="/replay", tags=["replay"])

# The saved demos, in the order the dropdown shows them. To add one, record a run with
# `manage.py record_case` (or build a scripted case) and add a row here.
REPLAY_CASES: list[dict[str, str]] = [
    {"id": "plan_ps236_bronx", "label": "P.S. 236, Bronx", "kind": "recorded",
     "tag": "Goal reachable but over budget; the city rates the roof not solar ready"},
    {"id": "plan_ps38_staten_island", "label": "P.S. 38, Staten Island", "kind": "recorded",
     "tag": "Goal reached within budget; the roof is over 20 years old and not rated solar ready"},
    {"id": "plan_red_hook_rec_center", "label": "Red Hook Recreation Center, Brooklyn", "kind": "recorded",
     "tag": "Landmark on parkland with a Sandy flood history"},
    {"id": "plan_jefferson_market_library", "label": "Jefferson Market Library, Manhattan", "kind": "recorded",
     "tag": "Pitched roof: needs an engineer or roofer before solar is sized"},
    {"id": "plan_ps24_bronx_existing_solar", "label": "P.S. 24, Bronx", "kind": "recorded",
     "tag": "Already has 228 kW of solar, with room for about 70 kW more; goal reached within budget"},
]
_BY_ID = {case["id"]: case for case in REPLAY_CASES}


def _case_model(case: dict[str, str]) -> schemas.ReplayCase:
    """The list row for one case, with the question the saved run was asked."""
    _, question = load_case(case["id"])
    return schemas.ReplayCase(id=case["id"], label=case["label"], tag=case["tag"], kind=case["kind"], question=question)


def _available() -> list[dict[str, str]]:
    """Only cases whose saved script is on disk, so a missing file never shows up as a broken menu item."""
    return [case for case in REPLAY_CASES if (FIXTURES_ROOT / case["id"] / "scripted_llm.json").is_file()]


@router.get("/cases", response_model=schemas.ReplayCaseListResponse)
def list_replay_cases() -> schemas.ReplayCaseListResponse:
    """The saved demos the planner can replay."""
    return schemas.ReplayCaseListResponse(cases=[_case_model(case) for case in _available()])


def _replay(case_id: str) -> schemas.ReplayResponse:
    """
    Create a session from the case's intake and replay the saved run.

    The scripted model and the mock tool mode are forced here, for this request only, so nothing reaches Claude
    or a live service even when the server runs live. Called through sync_to_async because it uses the ORM.
    """
    profile, question = load_case(case_id)
    session = services.create_session(profile=profile, fixture_case=case_id)
    services.add_message(session, role="user", content=question)
    with forced_tool_mode("mock"):
        run = run_harness(session, question, llm_provider="scripted", tool_mode="mock")
    loaded = services.get_run_with_events(run.pk)
    assistant = Message.objects.filter(run_id=run.pk, role="assistant").order_by("-id").first()
    return schemas.ReplayResponse(
        session=schemas.SessionResponse.model_validate(session),
        message=schemas.MessageResponse.model_validate(assistant) if assistant else None,
        run=schemas.run_to_response(loaded),
        case=_case_model(_BY_ID[case_id]),
    )


@router.post("/{case_id}", response_model=schemas.ReplayResponse)
async def replay_case(case_id: str) -> schemas.ReplayResponse:
    """Replay one saved demo. Unknown or unavailable cases return 404."""
    if case_id not in {case["id"] for case in _available()}:
        raise HTTPException(status_code=404, detail=f"No saved demo named {case_id!r}.")
    return await sync_to_async(_replay)(case_id)
