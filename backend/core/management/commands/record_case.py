"""
Django management command: save a finished run as a replayable case (v6, for demos and UI work).

Example: python manage.py record_case --run 12 --case demo_red_hook
         python manage.py record_case --run 12 --case demo_red_hook --overwrite --write-expected

After this, the case replays for free: LLM_PROVIDER=scripted TOOL_MODE=mock python manage.py run_case --case demo_red_hook
The command never calls Claude. It reads the run from the database named in the environment (set FRITTS_TEST_DB
to read a run from a scratch database). See backend/agent/record.py for what is saved.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from agent.record import RecordError, record_run
from core.models import Run
from mocks.catalog import FIXTURES_ROOT


class Command(BaseCommand):
    help = "Save a finished run as a replayable fixture case. Never calls Claude."

    def add_arguments(self, parser):
        parser.add_argument("--run", type=int, required=True, help="Id of the finished run to record.")
        parser.add_argument("--case", required=True, help="Folder name to create under mocks/fixtures/.")
        parser.add_argument("--overwrite", action="store_true", help="Replace the case's existing data files and intake.")
        parser.add_argument(
            "--write-expected",
            action="store_true",
            help="Replay the case once (scripted, free) and save its status as expected.json, so run_evals covers it.",
        )

    def handle(self, *args, **options):
        try:
            run = Run.objects.get(pk=options["run"])
        except Run.DoesNotExist as exc:
            raise CommandError(f"No run with id {options['run']} in this database.") from exc
        try:
            summary = record_run(run, options["case"], overwrite=options["overwrite"])
        except RecordError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Recorded run {run.pk} as {options['case']} ({summary['tool_calls']} tool calls)"))
        self.stdout.write("  written: " + ", ".join(summary["written"]))
        if summary["kept"]:
            self.stdout.write("  kept (already there): " + ", ".join(summary["kept"]) + "  (use --overwrite to replace)")
        for warning in summary["warnings"]:
            self.stdout.write(self.style.WARNING(f"  warning: {warning}"))

        if options["write_expected"]:
            from agent.evals import run_eval_case

            case_dir = FIXTURES_ROOT / options["case"]
            (case_dir / "expected.json").write_text("{}\n", encoding="utf-8")
            result = run_eval_case(options["case"])
            replay = Run.objects.order_by("-pk").first()
            check4 = (replay.flags or {}).get("check4") or {}
            expected = {
                "_comment": f"Recorded from live run {run.pk}. A replay is free; expectations are what the replay gave when recorded.",
                "status": result.status,
                "check4_passed": bool(check4.get("passed")),
            }
            (case_dir / "expected.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
            self.stdout.write(f"  expected.json: status={result.status}, check4_passed={expected['check4_passed']}")
