import uuid

from django.db import models

from apps.common.models import TimeStampedModel


class StatusReportState(models.TextChoices):
    IN_PROGRESS = "in_progress", "In Progress"
    ACTION_REQUIRED = "action_required", "Action Required"
    ON_HOLD = "on_hold", "On Hold"
    COMPLETED = "completed", "Completed"
    CANCELED = "canceled", "Canceled"


class StatusReportItem(TimeStampedModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    owner_name = models.CharField(max_length=120)
    status = models.CharField(max_length=24, choices=StatusReportState.choices, default=StatusReportState.IN_PROGRESS)
    order_index = models.PositiveIntegerField(default=100)
    updated_by_display_name = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["order_index", "due_date", "id"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self) -> str:
        return self.title


class ReportSubscription(TimeStampedModel):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    requested_by_display_name = models.CharField(max_length=120, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["email"]
        indexes = [models.Index(fields=["is_verified", "is_active"])]

    def __str__(self) -> str:
        return self.email
