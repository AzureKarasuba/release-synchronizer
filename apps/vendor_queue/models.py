from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class VendorActionType(models.TextChoices):
    UPDATE_ADO = "update_ado", "Update Azure DevOps"
    CONFIRM_DELIVERY = "confirm_delivery", "Confirm Delivery"
    PROVIDE_ETA = "provide_eta", "Provide ETA"


class VendorActionStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    BLOCKED = "blocked", "Blocked"
    PENDING_REVIEW = "pending_review", "Pending Review"
    DONE = "done", "Done"


class VendorAction(TimeStampedModel):
    release_item = models.ForeignKey("releases.ReleaseItem", on_delete=models.CASCADE, related_name="vendor_actions")
    vendor_name = models.CharField(max_length=150)
    vendor_contact_email = models.EmailField(blank=True)
    action_type = models.CharField(max_length=32, choices=VendorActionType.choices)
    status = models.CharField(max_length=24, choices=VendorActionStatus.choices, default=VendorActionStatus.OPEN)
    due_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_vendor_actions")
    last_vendor_update_at = models.DateTimeField(null=True, blank=True)
    stale_after_days = models.PositiveSmallIntegerField(default=7)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["status", "due_date", "id"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self) -> str:
        return f"{self.vendor_name} - {self.action_type}"
