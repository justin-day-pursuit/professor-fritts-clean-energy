"""
Django settings for Professor Fritts.

Loads the root .env (one level above backend/), uses local SQLite when DATABASE_URL
is empty, and uses Supabase Postgres when DATABASE_URL is a postgres URL.
Ensures backend/.data exists for the SQLite file and future uploads.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import dj_database_url
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


def _sqlite_config(name: str) -> dict:
    """Django database dict for a SQLite file. Tests and local dev both use this shape."""
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": name,
    }


def _database_config() -> dict:
    """
    Choose the database.

    Pytest always uses SQLite so the suite never opens Supabase. An empty
    DATABASE_URL also stays on SQLite under .data/. A postgres URL uses the
    session pooler (port 5432) with SSL required. This does not open a second
    psycopg pool; Django reuses one connection for up to 10 minutes.
    """
    test_db = os.environ.get("FRITTS_TEST_DB", "").strip()
    if test_db:
        return _sqlite_config(test_db)

    if "pytest" in sys.modules:
        return _sqlite_config(str(DATA_DIR / "pytest.sqlite3"))

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        return _sqlite_config(str(DATA_DIR / "dev.sqlite3"))

    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "", 1)
        return _sqlite_config(db_path)

    if database_url.startswith(("http://", "https://")):
        raise ValueError(
            "DATABASE_URL is a Supabase project URL. Django needs the session pooler "
            "Postgres URI from the dashboard Connect panel: port 5432, the database "
            "password, and ?sslmode=require."
        )

    if database_url.startswith(("postgres://", "postgresql://")):
        # conn_max_age keeps the connection open between requests. Health checks
        # drop it if Supabase already closed the idle session.
        config = dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
        options = config.setdefault("OPTIONS", {})
        options.setdefault("sslmode", "require")
        return config

    raise ValueError(
        "DATABASE_URL must be empty, sqlite:///, or a postgres:// / postgresql:// URL."
    )


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", default=True)

_allowed = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [host.strip() for host in _allowed.split(",") if host.strip()]
render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)

_csrf_trusted = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted.split(",") if o.strip()]
if render_host and f"https://{render_host}" not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

# Trust reverse proxies (such as Render) terminating SSL and forwarding HTTPS proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
