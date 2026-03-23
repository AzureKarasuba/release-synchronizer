from django.conf import settings
from django.db import models

from apps.common.constants import RoleType
from apps.common.models import TimeStampedModel


class RoleAssignment(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.CharField(max_length=64, choices=RoleType.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "role")
        indexes = [models.Index(fields=["role", "is_active"])]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.role}"
