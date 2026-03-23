from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0002_story_sync_models"),
        ("releases", "0002_releaseplan_azure_fields"),
        ("mappings", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ManualTicketAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assignment_mode",
                    models.CharField(
                        choices=[("azure_default", "Azure Default"), ("manual", "Manual Override")],
                        default="azure_default",
                        max_length=20,
                    ),
                ),
                ("override_reason", models.TextField(blank=True)),
                (
                    "release_plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="manual_ticket_assignments",
                        to="releases.releaseplan",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_manual_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "work_item",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="manual_assignment",
                        to="integrations.adouserstory",
                    ),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["assignment_mode"], name="manual_assign_mode_idx")],
            },
        ),
    ]
