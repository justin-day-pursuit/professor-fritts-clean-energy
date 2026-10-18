"""
FastAPI application factory — CORS for the Next.js frontend and API routers.

Django admin is mounted separately in fritts.asgi; this app owns /api/* routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import dev, documents, health, messages, plans, records, replay, runs, sessions
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

    for origin in ("http://localhost:3000", "https://professor-fritts-clean-energy.vercel.app"):
        if origin not in allowed_origins:
            allowed_origins.append(origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"^https://.*\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict[str, str]:
        """Root endpoint confirming service is alive for health checks and browsers."""
        return {"status": "ok", "service": "professor-fritts-backend", "version": "0.1.0"}

    # Expose health at both /health (Render default) and /api/health.
    app.include_router(health.router)
    app.include_router(health.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(messages.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    app.include_router(plans.router, prefix="/api")
    app.include_router(records.router, prefix="/api")
    app.include_router(replay.router, prefix="/api")
    app.include_router(dev.router, prefix="/api")
    return app
