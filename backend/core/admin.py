"""
Django admin screens so operators can inspect sessions, runs, and chat without SQL.

Register new models here with list_display columns that help debugging.
"""

from django.contrib import admin

from core import models


@admin.register(models.Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at")
    search_fields = ("id", "status")
    readonly_fields = ("id", "created_at")


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("filename", "session", "content_type", "size_bytes", "created_at")
    list_filter = ("content_type",)
    search_fields = ("filename", "session__id")


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "created_at", "run")
    list_filter = ("role",)
    search_fields = ("content",)


@admin.register(models.Run)
class RunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "status",
        "tool_mode",
        "llm_provider",
        "tool_call_count",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "tool_mode", "llm_provider")
    search_fields = ("session__id",)


@admin.register(models.RunEvent)
class RunEventAdmin(admin.ModelAdmin):
    list_display = ("run", "seq", "kind", "created_at")
    list_filter = ("kind",)
    ordering = ("run", "seq")
