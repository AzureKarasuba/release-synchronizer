from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class MappingSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    IMPORTED = "imported", "Imported"


class ReleaseSprintMapping(TimeStampedModel):
    release_item = models.ForeignKey("releases.ReleaseItem", on_delete=models.CASCADE, related_name="sprint_mappings")
    sprint_snapshot = models.ForeignKey("integrations.ADOSprintSnapshot", on_delete=models.CASCADE, related_name="release_mappings")
    mapping_source = models.CharField(max_length=20, choices=MappingSource.choices, default=MappingSource.MANUAL)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_release_mappings")

    class Meta:
        unique_together = ("release_item", "sprint_snapshot")
        indexes = [models.Index(fields=["mapping_source"])]

    def __str__(self) -> str:
        return f"{self.release_item_id} -> {self.sprint_snapshot_id}"
