from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView

from apps.audit.models import AuditEvent
from apps.common.constants import RoleType
from apps.common.permissions import user_has_any_role


class AuditEventListView(ListView):
    template_name = "audit/audit_event_list.html"
    model = AuditEvent
    context_object_name = "events"
    paginate_by = 50
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.EXECUTIVE_VIEWER,
        RoleType.SYSTEM_ADMIN,
    )

    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "DEMO_PUBLIC_MODE", False):
            return super().dispatch(request, *args, **kwargs)
        if user_has_any_role(request.user, self.allowed_roles):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied
