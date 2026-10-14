"""
Combined ASGI application: FastAPI for /api, Django for /admin on one port.

Run from the backend directory: uvicorn fritts.asgi:app --host 127.0.0.1 --port 8000
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fritts.settings")

# Django must initialize before importing code that touches settings or the ORM.
django_asgi_app = get_asgi_application()

from api.main import create_app  # noqa: E402
from django.conf import settings  # noqa: E402

fastapi_app = create_app()

# Mount Django so staff can use /admin/login/ while the product uses FastAPI routes.
fastapi_app.mount("/admin", django_asgi_app)

if settings.DEBUG:
    from django.contrib.staticfiles import finders
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    @fastapi_app.get("/static/{full_path:path}")
    async def serve_debug_static(full_path: str) -> FileResponse:
        """
        In DEBUG only: serve Django app static files (admin CSS/JS under /static/admin/…) so the local admin UI loads.

        Keeps /admin usable on one uvicorn port.
        """
        resolved = finders.find(full_path)
        if not resolved:
            raise HTTPException(status_code=404, detail="Static file not found")
        return FileResponse(resolved)
elif settings.STATIC_ROOT.exists():
    from fastapi.staticfiles import StaticFiles

    fastapi_app.mount("/static", StaticFiles(directory=str(settings.STATIC_ROOT)), name="static")

app = fastapi_app
# Django's ASGI_APPLICATION setting looks for this name.
application = app
