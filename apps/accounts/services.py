from apps.common.constants import RoleType
from apps.accounts.models import RoleAssignment


DEFAULT_ROLES = [choice[0] for choice in RoleType.choices]


def assign_role(*, user, role: str) -> RoleAssignment:
    assignment, _ = RoleAssignment.objects.update_or_create(
        user=user,
        role=role,
        defaults={"is_active": True},
    )
    return assignment
