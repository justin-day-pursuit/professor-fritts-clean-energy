from django.apps import AppConfig
from django.db import connections
from django.db.models.signals import post_migrate


def lock_public_tables(sender, **kwargs):
    """
    After migrations, lock every ordinary table in public.

    Supabase exposes the public schema through the Data API. Forced row level
    security with no policies lets the postgres role (which bypasses RLS) keep
    using Django, and blocks anon and authenticated. SQLite tests skip this.
    """
    if kwargs.get("using", "default") != "default":
        return

    connection = connections["default"]
    if connection.vendor != "postgresql":
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        cursor.execute(
            "SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')"
        )
        api_roles = [row[0] for row in cursor.fetchall()]

        for table in tables:
            quoted_table = connection.ops.quote_name(table)
            cursor.execute(
                f"ALTER TABLE public.{quoted_table} ENABLE ROW LEVEL SECURITY"
            )
            cursor.execute(
                f"ALTER TABLE public.{quoted_table} FORCE ROW LEVEL SECURITY"
            )
            # PUBLIC is the built-in group every role belongs to.
            cursor.execute(f"REVOKE ALL ON TABLE public.{quoted_table} FROM PUBLIC")
            for role in api_roles:
                quoted_role = connection.ops.quote_name(role)
                cursor.execute(
                    f"REVOKE ALL ON TABLE public.{quoted_table} FROM {quoted_role}"
                )


class CoreConfig(AppConfig):
    """Registers the core app where sessions, runs, and chat data live."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Professor Fritts core data"

    def ready(self):
        """Run the public-schema lock after each migrate, once per core app."""
        post_migrate.connect(lock_public_tables, sender=self)
