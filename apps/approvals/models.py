from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class CostApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class CostApproval(TimeStampedModel):
    release_item = models.OneToOneField("releases.ReleaseItem", on_delete=models.CASCADE, related_name="cost_approval")
    status = models.CharField(max_length=20, choices=CostApprovalStatus.choices, default=CostApprovalStatus.PENDING)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_cost_items")
    approval_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"CostApproval({self.release_item_id}, {self.status})"
