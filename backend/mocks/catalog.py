"""
Lists mock situations the dev landing page can run.

Each situation is a folder under mocks/fixtures that contains intake.json.
Add a folder there and it shows up on the landing page without a frontend change.
The default question matches manage.py run_case so the browser and the CLI start
from the same sentence.
"""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"

DEFAULT_QUESTION = (
    "How can we cut grid power 30% by 2030 on $400k and stay open as a "
    "cooling center during outages?"
)


def list_fixtures() -> list[dict]:
    """
    Return one summary per fixture folder that has an intake file.

    Sorted by folder name so the landing page order stays stable.
    """
    if not FIXTURES_ROOT.is_dir():
        return []
    summaries = []
    for folder in sorted(path for path in FIXTURES_ROOT.iterdir() if path.is_dir()):
        intake_path = folder / "intake.json"
        if not intake_path.is_file():
            continue
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
        summaries.append(
            {
                "id": folder.name,
                "building_name": str(intake.get("building_name") or folder.name),
                "goal": str(intake.get("goal") or ""),
                "question": str(intake.get("question") or DEFAULT_QUESTION),
            }
        )
    return summaries


def load_case(case: str) -> tuple[dict, str]:
    """
    Load intake profile and the question for one fixture folder.

    Raises FileNotFoundError when the folder or intake.json is missing, or when
    the name is not a single folder under fixtures (no slashes or parent hops).
    Strips the _comment key so it is not stored as building data.
    """
    if not case or "/" in case or "\\" in case or case.startswith("."):
        raise FileNotFoundError(case)
    folder = (FIXTURES_ROOT / case).resolve()
    if FIXTURES_ROOT.resolve() not in folder.parents:
        raise FileNotFoundError(case)
    intake_path = folder / "intake.json"
    if not intake_path.is_file():
        raise FileNotFoundError(case)
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    question = str(intake.pop("question", None) or DEFAULT_QUESTION)
    intake.pop("_comment", None)
    return intake, question
