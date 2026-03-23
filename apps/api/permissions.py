from rest_framework.permissions import BasePermission

from apps.common.constants import RoleType
from apps.common.permissions import is_internal_staff, user_has_role


class HasInternalStaffRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return is_internal_staff(user)


class HasRole(BasePermission):
    allowed_roles: tuple[str, ...] = tuple()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return any(user_has_role(user, role) for role in self.allowed_roles)


class CanManageMismatch(HasRole):
    allowed_roles = (RoleType.RELEASE_MANAGER, RoleType.ENGINEERING_LEAD, RoleType.SYSTEM_ADMIN)


class CanManageVendorActions(HasRole):
    allowed_roles = (RoleType.VENDOR_COORDINATOR, RoleType.VENDOR_USER, RoleType.RELEASE_MANAGER, RoleType.SYSTEM_ADMIN)


class CanImportSprintSnapshots(HasRole):
    allowed_roles = (RoleType.RELEASE_MANAGER, RoleType.ENGINEERING_LEAD, RoleType.SYSTEM_ADMIN)
