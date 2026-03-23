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
            name="RoleAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("release_manager", "Release Manager"),
                            ("engineering_lead", "Engineering Lead"),
                            ("finance_approver", "Finance Approver"),
                            ("vendor_coordinator", "Vendor Coordinator"),
                            ("vendor_user", "Vendor User"),
                            ("executive_viewer", "Executive Viewer"),
                            ("system_admin", "System Admin"),
                        ],
                        max_length=64,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["role", "is_active"], name="accounts_ro_role_3be4af_idx")],
                "unique_together": {("user", "role")},
            },
        ),
    ]
