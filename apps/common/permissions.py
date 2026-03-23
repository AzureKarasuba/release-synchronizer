from django.contrib.auth.mixins import UserPassesTestMixin

from apps.accounts.models import RoleAssignment
from apps.common.constants import RoleType


COST_VISIBLE_ROLES = {
    RoleType.RELEASE_MANAGER,
    RoleType.FINANCE_APPROVER,
    RoleType.SYSTEM_ADMIN,
}


INTERNAL_STAFF_ROLES = {
    RoleType.RELEASE_MANAGER,
    RoleType.ENGINEERING_LEAD,
    RoleType.FINANCE_APPROVER,
    RoleType.VENDOR_COORDINATOR,
    RoleType.EXECUTIVE_VIEWER,
    RoleType.SYSTEM_ADMIN,
}


def user_has_role(user, role: str) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return RoleAssignment.objects.filter(user=user, role=role, is_active=True).exists()


def user_has_any_role(user, roles: set[str] | tuple[str, ...]) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return RoleAssignment.objects.filter(user=user, role__in=roles, is_active=True).exists()


def can_view_cost(user) -> bool:
    return user_has_any_role(user, COST_VISIBLE_ROLES)


def is_internal_staff(user) -> bool:
    return user_has_any_role(user, INTERNAL_STAFF_ROLES)


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles: tuple[str, ...] = tuple()
    raise_exception = True

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not self.allowed_roles:
            return True
        return RoleAssignment.objects.filter(
            user=user,
            role__in=self.allowed_roles,
            is_active=True,
        ).exists()
