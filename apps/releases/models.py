from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel


class ReleasePlanStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"


class ReleaseItemStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    READY = "ready", "Ready"
    IN_PROGRESS = "in_progress", "In Progress"
    DELIVERED = "delivered", "Delivered"
    BLOCKED = "blocked", "Blocked"


class ReleasePlan(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    business_unit = models.CharField(max_length=120)
    status = models.CharField(max_length=24, choices=ReleasePlanStatus.choices, default=ReleasePlanStatus.DRAFT)
    target_start_date = models.DateField(null=True, blank=True)
    target_end_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_release_plans")

    # Auto-generated releases mirror Azure sprint categories by default.
    is_auto_generated = models.BooleanField(default=False)
    default_azure_iteration_path = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class ReleaseItem(TimeStampedModel):
    release_plan = models.ForeignKey(ReleasePlan, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=ReleaseItemStatus.choices, default=ReleaseItemStatus.PLANNED)
    target_release_date = models.DateField(null=True, blank=True)
    cost_estimate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    manual_override = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True)
    override_updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="override_release_items")
    override_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["target_release_date", "id"]

    def clean(self) -> None:
        super().clean()
        if self.manual_override and not self.override_reason.strip():
            raise ValidationError({"override_reason": "Override reason is required when manual override is enabled."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
