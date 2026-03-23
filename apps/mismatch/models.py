from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class FindingSeverity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class FindingStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"
    IGNORED = "ignored", "Ignored"


class FindingType(models.TextChoices):
    MISSING_APPROVAL = "missing_approval", "Missing Cost Approval"
    STALE_VENDOR_UPDATE = "stale_vendor_update", "Stale Vendor Update"
    UNMAPPED_RELEASE_ITEM = "unmapped_release_item", "Unmapped Release Item"


class MismatchFinding(TimeStampedModel):
    fingerprint = models.CharField(max_length=140, unique=True)
    finding_type = models.CharField(max_length=40, choices=FindingType.choices)
    severity = models.CharField(max_length=16, choices=FindingSeverity.choices, default=FindingSeverity.MEDIUM)
    status = models.CharField(max_length=20, choices=FindingStatus.choices, default=FindingStatus.OPEN)
    release_item = models.ForeignKey("releases.ReleaseItem", null=True, blank=True, on_delete=models.CASCADE, related_name="mismatch_findings")
    vendor_action = models.ForeignKey("vendor_queue.VendorAction", null=True, blank=True, on_delete=models.CASCADE, related_name="mismatch_findings")
    details = models.JSONField(default=dict, blank=True)
    detected_at = models.DateTimeField()
    last_checked_at = models.DateTimeField()
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_findings")
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="resolved_findings")
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "severity"]), models.Index(fields=["finding_type", "status"])]
        ordering = ["status", "-severity", "-detected_at"]

    def __str__(self) -> str:
        return f"{self.finding_type}:{self.fingerprint}"
