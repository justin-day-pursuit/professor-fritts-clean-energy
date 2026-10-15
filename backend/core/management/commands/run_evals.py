"""
Django management command — run every eval case and report pass or fail (v6 goalpost).

Example: python manage.py run_evals            (scripted model, mock tools)
         python manage.py run_evals --case case3_park_rec_center
         python manage.py run_evals --llm anthropic --tool-mode live
Exits non-zero when any case misses an expectation in its expected.json.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from agent.evals import list_eval_cases, run_eval_case


class Command(BaseCommand):
    help = "Run the eval cases and compare each run to its expected.json."

    def add_arguments(self, parser):
        parser.add_argument("--case", action="append", help="Run only this case (repeatable).")
        parser.add_argument("--llm", choices=["scripted", "anthropic"], default="scripted")
        parser.add_argument("--tool-mode", choices=["mock", "live"], default="mock")

    def handle(self, *args, **options):
        cases = options.get("case") or list_eval_cases()
        unknown = sorted(set(cases) - set(list_eval_cases()))
        if unknown:
            raise CommandError(f"No expected.json for: {', '.join(unknown)}")

        llm = options["llm"]
        tool_mode = options["tool_mode"]
        self.stdout.write(f"Running {len(cases)} cases with llm={llm} tool_mode={tool_mode}")

        failed = 0
        for case in cases:
            result = run_eval_case(case, llm_provider=llm, tool_mode=tool_mode)
            label = f"{case}  (status={result.status}, run={result.run_id}, llm={result.llm_provider}, tools={result.tool_mode})"
            if result.passed:
                self.stdout.write(self.style.SUCCESS(f"PASS  {label}"))
                continue
            failed += 1
            self.stdout.write(self.style.ERROR(f"FAIL  {label}"))
            for failure in result.failures:
                self.stdout.write(f"      - {failure}")

        self.stdout.write(f"\n{len(cases) - failed}/{len(cases)} eval cases passed.")
        if failed:
            raise SystemExit(1)
