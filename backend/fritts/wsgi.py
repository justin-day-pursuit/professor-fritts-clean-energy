"""WSGI entry for traditional servers; the dev stack uses ASGI (fritts.asgi) instead."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fritts.settings")

application = get_wsgi_application()
