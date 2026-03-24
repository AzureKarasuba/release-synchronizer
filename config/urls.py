from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("api/", include("apps.api.urls")),

    # Primary product flow
    path("", include("apps.coordination.urls")),
    path("audit/", include("apps.audit.urls")),

    # Legacy/internal pages kept for reference during transition
    path("legacy/releases/", include("apps.releases.urls")),
    path("legacy/approvals/", include("apps.approvals.urls")),
    path("legacy/mappings/", include("apps.mappings.urls")),
    path("legacy/vendor-actions/", include("apps.vendor_queue.urls")),
    path("legacy/mismatch/", include("apps.mismatch.urls")),
    path("legacy/audit/", include("apps.audit.urls")),
]
