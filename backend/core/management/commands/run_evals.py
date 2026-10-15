"""
Django management command — run every eval case in mock mode and report pass or fail (v6 goalpost).

Example: python manage.py run_evals            (all cases)
         python manage.py run_evals --case case3_park_rec_center
Exits non-zero when any case misses an expectation in its expected.json.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from agent.evals import list_eval_cases, run_eval_case


class Command(BaseCommand):
    help = "Run the eval cases (scripted model, mock tools) and compare each run to its expected.json."

    def add_arguments(self, parser):
        parser.add_argument("--case", action="append", help="Run only this case (repeatable).")

    def handle(self, *args, **options):
        cases = options.get("case") or list_eval_cases()
        unknown = sorted(set(cases) - set(list_eval_cases()))
        if unknown:
            raise CommandError(f"No expected.json for: {', '.join(unknown)}")

        failed = 0
        for case in cases:
            result = run_eval_case(case)
            if result.passed:
                self.stdout.write(self.style.SUCCESS(f"PASS  {case}  (status={result.status})"))
                continue
            failed += 1
            self.stdout.write(self.style.ERROR(f"FAIL  {case}  (status={result.status})"))
            for failure in result.failures:
                self.stdout.write(f"      - {failure}")

        self.stdout.write(f"\n{len(cases) - failed}/{len(cases)} eval cases passed.")
        if failed:
            raise SystemExit(1)
