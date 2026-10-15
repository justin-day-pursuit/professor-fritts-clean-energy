"""
Django management command — the v2 goalpost script.

Runs an eval case and confirms 100% of the numbers in the plan have a label, a confidence and an
ID, and that the plan has all 13 sections in order. Exits non-zero if either check fails.

Example: LLM_PROVIDER=scripted TOOL_MODE=mock python manage.py check_coverage --case case1_queens_library
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from agent.claims import SECTION_TITLES, RoadmapPayload
from agent.coverage import check_coverage
from agent.harness import run_harness
from core import services

FIXTURES = Path(__file__).resolve().parents[3] / "mocks" / "fixtures"


class Command(BaseCommand):
    help = "Run a case and confirm every number has a label, confidence and ID, with all 13 sections."

    def add_arguments(self, parser):
        parser.add_argument("--case", default="case1_queens_library")
        parser.add_argument("--llm", choices=["scripted", "anthropic"], default="scripted")

    def handle(self, *args, **options):
        case = options["case"]
        intake_path = FIXTURES / case / "intake.json"
        if not intake_path.exists():
            raise CommandError(f"No intake fixture for case {case!r}")
        profile = json.loads(intake_path.read_text(encoding="utf-8"))
        profile.pop("_comment", None)

        question = "How can we cut grid power 30% by 2030 on $400k and stay open as a cooling center?"
        session = services.create_session(profile=profile, fixture_case=case)
        services.add_message(session, role="user", content=question)
        run = services.get_run_with_events(run_harness(session, question, llm_provider=options["llm"]).pk)

        roadmap = (run.output or {}).get("roadmap")
        if not roadmap:
            raise CommandError(f"Run ended with status {run.status} and no roadmap to check.")
        payload = RoadmapPayload.model_validate(roadmap)

        report = check_coverage(payload)
        self.stdout.write(
            f"Numeric claims: {report.numeric_claims}, covered: {report.covered} ({report.percent:.0f}%)"
        )
        for failure in report.failures:
            self.stdout.write(f"  MISSING {failure['missing']} in section {failure['section']}: {failure['text']}")

        # The rendered markdown always lists all 13 headings; check they appear in PRD order.
        markdown = (run.output or {}).get("markdown", "")
        headings = [f"## {sid}. {title}" for sid, title in SECTION_TITLES.items()]
        positions = [markdown.find(h) for h in headings]
        in_order = all(p >= 0 for p in positions) and positions == sorted(positions)
        self.stdout.write(f"13 sections in order: {'yes' if in_order else 'NO'}")

        if not (report.complete and in_order):
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("v2 goalpost: PASS"))
