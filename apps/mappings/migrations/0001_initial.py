from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("integrations", "0001_initial"),
        ("releases", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReleaseSprintMapping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "mapping_source",
                    models.CharField(choices=[("manual", "Manual"), ("imported", "Imported")], default="manual", max_length=20),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_release_mappings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "release_item",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sprint_mappings", to="releases.releaseitem"),
                ),
                (
                    "sprint_snapshot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="release_mappings",
                        to="integrations.adosprintsnapshot",
                    ),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["mapping_source"], name="mappings_re_mappin_03666f_idx")],
                "unique_together": {("release_item", "sprint_snapshot")},
            },
        ),
    ]
