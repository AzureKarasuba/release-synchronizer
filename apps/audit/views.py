from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.audit.models import AuditEvent
from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin


class AuditEventListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "audit/audit_event_list.html"
    model = AuditEvent
    context_object_name = "events"
    paginate_by = 50
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.EXECUTIVE_VIEWER,
        RoleType.SYSTEM_ADMIN,
    )
