from django.conf import settings
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


class IntegrationSyncState(models.Model):
    key = models.CharField(max_length=120, unique=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=20, default="never")
    last_error = models.TextField(blank=True)
    last_batch_id = models.UUIDField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["key"])]

    def __str__(self) -> str:
        return f"{self.key}:{self.last_status}"


class ADOUserStory(TimeStampedModel):
    work_item_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255)
    assigned_to = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=80, blank=True)
    sprint_path = models.CharField(max_length=255, blank=True)
    sprint_name = models.CharField(max_length=200, blank=True)
    target_date = models.DateField(null=True, blank=True)
    changed_date = models.DateTimeField(null=True, blank=True)
    azure_url = models.URLField(blank=True)

    # Internal coordination fields shown in mirror/manual views.
    cost_approved = models.BooleanField(default=False)
    cost_approved_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    raw_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["sprint_name", "target_date", "work_item_id"]
        indexes = [
            models.Index(fields=["is_active", "sprint_name"]),
            models.Index(fields=["work_item_id"]),
            models.Index(fields=["state"]),
        ]

    def __str__(self) -> str:
        return f"#{self.work_item_id} {self.title}"


class AzureWritebackRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPLIED = "applied", "Applied"
        FAILED = "failed", "Failed"

    work_item = models.ForeignKey(ADOUserStory, on_delete=models.CASCADE, related_name="writeback_requests")
    target_iteration_path = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="azure_writeback_requests")
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"{self.work_item_id} -> {self.target_iteration_path} ({self.status})"
