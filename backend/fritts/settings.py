"""
Django settings for Professor Fritts.

Loads the root .env (one level above backend/), uses local SQLite when DATABASE_URL
is empty, and ensures backend/.data exists for the database and future uploads.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# backend/ is the Django BASE_DIR; the repo root (parent) holds .env.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# Local data directory for SQLite, uploads, and cache (gitignored at runtime).
DATA_DIR = BASE_DIR / ".data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _env_bool(name: str, default: bool = False) -> bool:
    """Read a true/false string from the environment."""
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _database_config() -> dict:
    """
    Choose the database: Postgres URL when set, otherwise SQLite under .data/.
    During pytest, use an in-memory SQLite so tests do not touch dev.sqlite3.
    """
    test_db = os.environ.get("FRITTS_TEST_DB", "").strip()
    if test_db:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": test_db,
        }

    if "pytest" in sys.modules:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(DATA_DIR / "pytest.sqlite3"),
        }

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        # Minimal sqlite URL support for future local overrides; Postgres URLs need dj-database-url later.
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "", 1)
            return {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": db_path,
            }
        raise ValueError(
            "Non-empty DATABASE_URL must be sqlite:/// for v0, or configure Postgres in a later block."
        )

    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATA_DIR / "dev.sqlite3"),
    }


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", default=True)

_allowed = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [host.strip() for host in _allowed.split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fritts.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "fritts.wsgi.application"
ASGI_APPLICATION = "fritts.asgi.application"

DATABASES = {"default": _database_config()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = DATA_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Values exposed on the health endpoint (read from root .env).
TOOL_MODE = os.environ.get("TOOL_MODE", "mock")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
