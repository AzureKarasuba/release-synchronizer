from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ADOSprintSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("snapshot_batch_id", models.UUIDField()),
                ("source_project", models.CharField(max_length=120)),
                ("external_sprint_id", models.CharField(max_length=100)),
                ("sprint_name", models.CharField(max_length=200)),
                ("iteration_path", models.CharField(max_length=255)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("state", models.CharField(blank=True, max_length=40)),
            ],
            options={
                "indexes": [models.Index(fields=["source_project", "external_sprint_id"], name="integ_src_ext_7f9ef6_idx")],
                "unique_together": {("snapshot_batch_id", "external_sprint_id")},
            },
        ),
    ]
