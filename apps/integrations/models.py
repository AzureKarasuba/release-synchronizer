from django.db import models

from apps.common.models import TimeStampedModel


class ADOSprintSnapshot(TimeStampedModel):
    snapshot_batch_id = models.UUIDField()
    source_project = models.CharField(max_length=120)
    external_sprint_id = models.CharField(max_length=100)
    sprint_name = models.CharField(max_length=200)
    iteration_path = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    state = models.CharField(max_length=40, blank=True)

    class Meta:
        unique_together = ("snapshot_batch_id", "external_sprint_id")
        indexes = [models.Index(fields=["source_project", "external_sprint_id"])]

    def __str__(self) -> str:
        return f"{self.source_project}:{self.sprint_name}"
