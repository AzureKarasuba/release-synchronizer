from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("api/", include("apps.api.urls")),
    path("", include("apps.releases.urls")),
    path("approvals/", include("apps.approvals.urls")),
    path("mappings/", include("apps.mappings.urls")),
    path("vendor-actions/", include("apps.vendor_queue.urls")),
    path("mismatch/", include("apps.mismatch.urls")),
    path("audit/", include("apps.audit.urls")),
]
