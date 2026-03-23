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
            name="CostApproval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("approval_date", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "approver",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_cost_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "release_item",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="cost_approval", to="releases.releaseitem"),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
    ]
