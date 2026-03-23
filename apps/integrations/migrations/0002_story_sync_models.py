from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IntegrationSyncState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=120, unique=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("last_status", models.CharField(default="never", max_length=20)),
                ("last_error", models.TextField(blank=True)),
                ("last_batch_id", models.UUIDField(blank=True, null=True)),
            ],
            options={
                "indexes": [models.Index(fields=["key"], name="integ_sync_key_23dd2e_idx")],
            },
        ),
        migrations.CreateModel(
            name="ADOUserStory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("work_item_id", models.BigIntegerField(unique=True)),
                ("title", models.CharField(max_length=255)),
                ("assigned_to", models.CharField(blank=True, max_length=200)),
                ("state", models.CharField(blank=True, max_length=80)),
                ("sprint_path", models.CharField(blank=True, max_length=255)),
                ("sprint_name", models.CharField(blank=True, max_length=200)),
                ("target_date", models.DateField(blank=True, null=True)),
                ("changed_date", models.DateTimeField(blank=True, null=True)),
                ("azure_url", models.URLField(blank=True)),
                ("cost_approved", models.BooleanField(default=False)),
                ("cost_approved_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("raw_fields", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ["sprint_name", "target_date", "work_item_id"],
                "indexes": [
                    models.Index(fields=["is_active", "sprint_name"], name="ado_story_act_sprint_idx"),
                    models.Index(fields=["work_item_id"], name="ado_story_wi_idx"),
                    models.Index(fields=["state"], name="ado_story_state_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AzureWritebackRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "target_iteration_path",
                    models.CharField(max_length=255),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("applied", "Applied"), ("failed", "Failed")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="azure_writeback_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "work_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="writeback_requests",
                        to="integrations.adouserstory",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [models.Index(fields=["status", "created_at"], name="ado_write_status_cr_idx")],
            },
        ),
    ]
