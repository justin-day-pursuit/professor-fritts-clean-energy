"""
URL routes served by Django when mounted under /admin on the combined ASGI app.

Paths here are relative to the mount point, so admin login appears as /admin/login/ to browsers.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("", admin.site.urls),
]
