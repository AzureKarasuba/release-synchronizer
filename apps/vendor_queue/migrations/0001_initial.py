from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("releases", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="VendorAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("vendor_name", models.CharField(max_length=150)),
                ("vendor_contact_email", models.EmailField(blank=True, max_length=254)),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("update_ado", "Update Azure DevOps"),
                            ("confirm_delivery", "Confirm Delivery"),
                            ("provide_eta", "Provide ETA"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("in_progress", "In Progress"),
                            ("blocked", "Blocked"),
                            ("pending_review", "Pending Review"),
                            ("done", "Done"),
                        ],
                        default="open",
                        max_length=24,
                    ),
                ),
                ("due_date", models.DateField(blank=True, null=True)),
                ("last_vendor_update_at", models.DateTimeField(blank=True, null=True)),
                ("stale_after_days", models.PositiveSmallIntegerField(default=7)),
                ("notes", models.TextField(blank=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_vendor_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "release_item",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vendor_actions", to="releases.releaseitem"),
                ),
            ],
            options={
                "ordering": ["status", "due_date", "id"],
                "indexes": [models.Index(fields=["status", "due_date"], name="vendor_queu_status_8cfde2_idx")],
            },
        ),
    ]
