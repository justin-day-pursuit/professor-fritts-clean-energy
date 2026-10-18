"""
Django management command: set the saved demo buildings up from the city's records (v8).

Example: python manage.py build_city_intakes            (shows what would change; writes nothing)
         python manage.py build_city_intakes --write    (saves the new intake.json files)

For each building in the replay menu this reads the city's free records for its address (the same ones the website uses to
pre-fill the form) and replaces the hand-typed floor area, year built, yearly electricity, roof area and existing solar with the
city's values. What a visitor would type, the budget, goal, what must keep running in an outage and roof type, is left alone.
It makes no Claude calls and costs nothing. A building the city has no record for in some part keeps its typed value for that part.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from api.routers.replay import REPLAY_CASES
from mocks.catalog import FIXTURES_ROOT
from tools.city_intake import city_fields

# The profile fields the city can fill. Anything else in an intake is typed by a person and is never changed here.
CITY_FIELDS = ("address", "floor_area_sqft", "year_built", "annual_kwh", "roof_area_sqft", "existing_solar_kw")


class Command(BaseCommand):
    help = "Replace each demo building's hand-typed city details with the city's own records. Never calls Claude."

    def add_arguments(self, parser):
        parser.add_argument("--write", action="store_true", help="Save the new intake.json files (the default only shows the changes).")
        parser.add_argument("--case", action="append", help="Only this case id (repeat for several).")

    def handle(self, *args, **options):
        wanted = set(options["case"] or [])
        for case in REPLAY_CASES:
            case_id = case["id"]
            if wanted and case_id not in wanted:
                continue
            path = FIXTURES_ROOT / case_id / "intake.json"
            intake = json.loads(path.read_text(encoding="utf-8"))
            found = city_fields(str(intake["address"]), str(intake["borough"]))
            new = dict(intake)
            for name in CITY_FIELDS:
                if name in found["fields"]:
                    new[name] = found["fields"][name]
                elif name == "existing_solar_kw":
                    # The city lists no completed solar, so a typed size is not backed by a record; the visitor flow would leave it blank.
                    new.pop(name, None)

            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{case['label']}  ({found['found']['label']}, owner: {found['found']['owner']})"))
            for name in CITY_FIELDS:
                before, after = intake.get(name), new.get(name)
                mark = "  same   " if before == after else "  CHANGE "
                self.stdout.write(f"{mark}{name:18s} {before!s:>22}  ->  {after!s}")
            for line in found["missing"]:
                self.stdout.write(f"  (city has no record: {line})")
            if options["write"]:
                path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if not options["write"]:
            self.stdout.write("\nNothing was written. Run again with --write to save these.")
