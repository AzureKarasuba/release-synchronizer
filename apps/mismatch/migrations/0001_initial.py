from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("releases", "0001_initial"),
        ("vendor_queue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MismatchFinding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("fingerprint", models.CharField(max_length=140, unique=True)),
                (
                    "finding_type",
                    models.CharField(
                        choices=[
                            ("missing_approval", "Missing Cost Approval"),
                            ("stale_vendor_update", "Stale Vendor Update"),
                            ("unmapped_release_item", "Unmapped Release Item"),
                        ],
                        max_length=40,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
                        default="medium",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("in_progress", "In Progress"), ("resolved", "Resolved"), ("ignored", "Ignored")],
                        default="open",
                        max_length=20,
                    ),
                ),
                ("details", models.JSONField(blank=True, default=dict)),
                ("detected_at", models.DateTimeField()),
                ("last_checked_at", models.DateTimeField()),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_note", models.TextField(blank=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_findings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "release_item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mismatch_findings",
                        to="releases.releaseitem",
                    ),
                ),
                (
                    "resolved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resolved_findings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "vendor_action",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mismatch_findings",
                        to="vendor_queue.vendoraction",
                    ),
                ),
            ],
            options={
                "ordering": ["status", "-severity", "-detected_at"],
                "indexes": [
                    models.Index(fields=["status", "severity"], name="mismatch_mi_status_e4c34f_idx"),
                    models.Index(fields=["finding_type", "status"], name="mismatch_mi_finding_26c57b_idx"),
                ],
            },
        ),
    ]
