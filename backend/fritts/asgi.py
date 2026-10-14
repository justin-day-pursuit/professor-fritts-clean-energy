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

fastapi_app = create_app()

# Mount Django so staff can use /admin/login/ while the product uses FastAPI routes.
fastapi_app.mount("/admin", django_asgi_app)

app = fastapi_app
