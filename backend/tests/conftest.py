"""
Pytest fixtures: Django database migrated for tests, FastAPI TestClient on the combined app.
"""

from __future__ import annotations

import os
import tempfile

# Dedicated SQLite file before Django loads settings so tests never touch dev.sqlite3.
_test_db_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
os.environ["FRITTS_TEST_DB"] = _test_db_file.name
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fritts.settings")

import django
from django.core.management import call_command

django.setup()
call_command("migrate", verbosity=0, interactive=False)

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def api_client() -> TestClient:
    """HTTP client that talks to the same ASGI app uvicorn would serve."""
    from fritts.asgi import app

    return TestClient(app)
