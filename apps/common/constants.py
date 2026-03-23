from django.db.models import TextChoices


class RoleType(TextChoices):
    RELEASE_MANAGER = "release_manager", "Release Manager"
    ENGINEERING_LEAD = "engineering_lead", "Engineering Lead"
    FINANCE_APPROVER = "finance_approver", "Finance Approver"
    VENDOR_COORDINATOR = "vendor_coordinator", "Vendor Coordinator"
    VENDOR_USER = "vendor_user", "Vendor User"
    EXECUTIVE_VIEWER = "executive_viewer", "Executive Viewer"
    SYSTEM_ADMIN = "system_admin", "System Admin"
