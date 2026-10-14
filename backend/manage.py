#!/usr/bin/env python
"""Django's command-line utility — run migrations, checks, and admin tasks from the backend folder."""

import os
import sys


def main() -> None:
    # Tell Django which settings module to load before any Django code runs.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fritts.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Activate backend/.venv and install requirements.txt."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
