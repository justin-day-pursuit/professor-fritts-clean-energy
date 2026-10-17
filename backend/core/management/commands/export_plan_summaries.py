"""
Django management command: write each saved demo's plan summary to a JSON file for design work (v7).

Example: python manage.py export_plan_summaries --out ../frontend/app/plan-mockup/data

It replays every case in the replay menu (free: scripted model, mock tools, so no Claude call and no network) and
saves the finished run's plan summary beside the case's label, question and intake, all in one plans.json. The design
pages read that file, so the layout can be edited while looking at a real run with no server and no cost.
Run it again after changing the summary or after recording a new case.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from agent.harness import run_harness
from api.routers.replay import REPLAY_CASES
from core import services
from mocks.catalog import load_case
from mocks.mock_mode import forced_tool_mode


class Command(BaseCommand):
    help = "Replay each saved demo (free) and write its plan summary to a JSON file."

    def add_arguments(self, parser):
        parser.add_argument("--out", required=True, help="Folder to write plans.json into.")

    def handle(self, *args, **options):
        out = Path(options["out"])
        out.mkdir(parents=True, exist_ok=True)
        plans = []
        for case in REPLAY_CASES:
            profile, question = load_case(case["id"])
            session = services.create_session(profile=profile, fixture_case=case["id"])
            with forced_tool_mode("mock"):
                run = run_harness(session, question, llm_provider="scripted", tool_mode="mock")
            output = run.output or {}
            payload = {
                "id": case["id"],
                "label": case["label"],
                "kind": case["kind"],
                "tag": case["tag"],
                "question": question,
                "status": run.status,
                "intake": profile,
                "plan_summary": output.get("plan_summary"),
                "markdown": output.get("markdown"),
            }
            plans.append(payload)
            self.stdout.write(f"replayed {case['id']} ({run.status})")
        (out / "plans.json").write_text(json.dumps(plans, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Exported {len(plans)} plan summaries to {out / 'plans.json'}"))
