# Generated for agent-harness: mock fixture case name per session.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="fixture_case",
            field=models.CharField(default="case1_queens_library", max_length=128),
        ),
    ]
