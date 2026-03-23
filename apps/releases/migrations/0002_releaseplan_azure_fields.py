from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("releases", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="releaseplan",
            name="default_azure_iteration_path",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="releaseplan",
            name="is_auto_generated",
            field=models.BooleanField(default=False),
        ),
    ]
