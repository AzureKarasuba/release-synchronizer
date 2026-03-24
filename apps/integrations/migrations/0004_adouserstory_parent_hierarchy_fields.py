# Generated manually for parent feature hierarchy support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0003_rename_integ_src_ext_7f9ef6_idx_integration_source__5056b0_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="adouserstory",
            name="parent_title",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="adouserstory",
            name="parent_work_item_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="adouserstory",
            name="parent_work_item_type",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddIndex(
            model_name="adouserstory",
            index=models.Index(fields=["parent_work_item_id"], name="integration_parent_wi_idx"),
        ),
    ]
