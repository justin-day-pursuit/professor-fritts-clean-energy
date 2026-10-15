"""
Save the live tool responses for eval case 1 as fixtures (build plan v1).

Run from the backend folder with the API keys in .env:  python -m mocks.save_live_fixtures
Files land in mocks/fixtures/<case>/live/ and mirror ToolResult, so a later run can replay real data.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

CASE = "case1_queens_library"
LIVE_TOOLS = ("get_solar_production", "get_utility_rates", "lookup_ny_building_records")


def main() -> None:
    """Run the three live tools on case 1 and write each response to the live fixtures folder."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fritts.settings")
    os.environ["TOOL_MODE"] = "live"
    import django

    django.setup()
    from django.conf import settings

    settings.TOOL_MODE = "live"
    from mocks.mock_mode import FIXTURES_ROOT
    from tools.registry import execute_tool

    folder = FIXTURES_ROOT / CASE
    profile = json.loads((folder / "intake.json").read_text(encoding="utf-8"))
    out_dir = folder / "live"
    out_dir.mkdir(exist_ok=True)
    for name in LIVE_TOOLS:
        result = execute_tool(name, {}, session_profile=profile, fixture_case=CASE)
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(result.model_dump(), indent=2) + "\n", encoding="utf-8")
        print(f"saved {path.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
