# Generated manually for story points support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0004_adouserstory_parent_hierarchy_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="adouserstory",
            name="story_points",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
