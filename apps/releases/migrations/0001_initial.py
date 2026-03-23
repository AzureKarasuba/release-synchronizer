from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReleasePlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=40, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("business_unit", models.CharField(max_length=120)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("active", "Active"), ("closed", "Closed")],
                        default="draft",
                        max_length=24,
                    ),
                ),
                ("target_start_date", models.DateField(blank=True, null=True)),
                ("target_end_date", models.DateField(blank=True, null=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_release_plans",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ReleaseItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planned", "Planned"),
                            ("ready", "Ready"),
                            ("in_progress", "In Progress"),
                            ("delivered", "Delivered"),
                            ("blocked", "Blocked"),
                        ],
                        default="planned",
                        max_length=24,
                    ),
                ),
                ("target_release_date", models.DateField(blank=True, null=True)),
                ("cost_estimate", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("manual_override", models.BooleanField(default=False)),
                ("override_reason", models.TextField(blank=True)),
                ("override_updated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "override_updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="override_release_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "release_plan",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="releases.releaseplan"),
                ),
            ],
            options={"ordering": ["target_release_date", "id"]},
        ),
    ]
