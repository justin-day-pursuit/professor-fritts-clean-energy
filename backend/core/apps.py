from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Registers the core app where sessions, runs, and chat data live."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Professor Fritts core data"
