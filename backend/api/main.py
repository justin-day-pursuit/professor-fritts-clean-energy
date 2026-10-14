"""
FastAPI application factory — CORS for the Next.js frontend and API routers.

Django admin is mounted separately in fritts.asgi; this app owns /api/* routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import documents, health, messages, runs, sessions
from django.conf import settings


def create_app() -> FastAPI:
    """Build the FastAPI app used by ASGI and pytest."""
    app = FastAPI(
        title="Professor Fritts API",
        description="Building renewable energy planner — backend API",
        version="0.1.0",
    )

    # Allow the browser frontend to call the API during local development.
    origin = getattr(settings, "FRONTEND_ORIGIN", "http://localhost:3000")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(messages.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    return app
