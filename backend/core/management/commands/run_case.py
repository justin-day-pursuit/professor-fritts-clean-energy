"""
Django management command — run an eval case through the harness (scripted or anthropic).

Example: LLM_PROVIDER=scripted TOOL_MODE=mock python manage.py run_case --case case1_queens_library --llm scripted
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from agent.harness import run_harness
from core import services
from core.models import Run

FIXTURES = Path(__file__).resolve().parents[3] / "mocks" / "fixtures"


class Command(BaseCommand):
    help = "Run a fixture eval case end-to-end and print the run log plus roadmap."

    def add_arguments(self, parser):
        parser.add_argument("--case", default="case1_queens_library")
        parser.add_argument("--llm", choices=["scripted", "anthropic"], default=None)
        parser.add_argument(
            "--message",
            default=(
                "How can we cut grid power 30% by 2030 on $400k and stay open as a "
                "cooling center during outages?"
            ),
        )

    def handle(self, *args, **options):
        case = options["case"]
        intake_path = FIXTURES / case / "intake.json"
        if not intake_path.exists():
            raise CommandError(f"No intake fixture for case {case!r}")

        profile = json.loads(intake_path.read_text(encoding="utf-8"))
        profile.pop("_comment", None)
        session = services.create_session(profile=profile, fixture_case=case)
        services.add_message(session, role="user", content=options["message"])

        try:
            run = run_harness(session, options["message"], llm_provider=options["llm"])
        except Exception as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            raise SystemExit(1) from exc

        run = services.get_run_with_events(run.pk)
        self.stdout.write(self.style.MIGRATE_HEADING(f"Run {run.pk} status={run.status}"))
        for event in run.events.all():
            if event.kind == "tool_call":
                self.stdout.write(f"  TOOL CALL: {event.payload.get('tool')} input={event.payload.get('input')}")
            elif event.kind == "tool_result":
                self.stdout.write(
                    f"  TOOL RESULT: mock={event.payload.get('mock')} source={event.payload.get('source_url')}"
                )
            elif event.kind.startswith("check"):
                self.stdout.write(f"  {event.kind.upper()}: passed={event.payload.get('passed')} {event.payload.get('message')}")

        markdown = (run.output or {}).get("markdown") or ""
        if markdown:
            self.stdout.write("\n--- Roadmap ---\n")
            self.stdout.write(markdown)

        if run.status == Run.Status.FAILED:
            err = (run.output or {}).get("error", "failed")
            self.stderr.write(self.style.ERROR(err))
            raise SystemExit(1)
        if run.status not in (Run.Status.DONE, Run.Status.PARTIAL, Run.Status.NEEDS_INPUT):
            raise SystemExit(1)
