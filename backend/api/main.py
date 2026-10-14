"""
FastAPI application factory — CORS for the Next.js frontend and API routers.

Django admin is mounted separately in fritts.asgi; this app owns /api/* routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import dev, documents, health, messages, runs, sessions
from django.conf import settings


def create_app() -> FastAPI:
    """Build the FastAPI app used by ASGI and pytest."""
    app = FastAPI(
        title="Professor Fritts API",
        description="Building renewable energy planner — backend API",
        version="0.1.0",
    )

    # Allow browser frontends (local and deployed) to call the API.
    origin_setting = getattr(settings, "FRONTEND_ORIGIN", "http://localhost:3000")
    if isinstance(origin_setting, str):
        allowed_origins = [o.strip() for o in origin_setting.split(",") if o.strip()]
    else:
        allowed_origins = list(origin_setting)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(messages.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    app.include_router(dev.router, prefix="/api")
    return app
