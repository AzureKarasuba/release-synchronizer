from django.urls import path

from apps.api.views import ADOSprintSnapshotImportAPIView, AuditEventListAPIView, ReleaseMismatchListAPIView, RunMismatchScanAPIView, VendorActionStatusAPIView

urlpatterns = [
    path("mismatch-scan/run", RunMismatchScanAPIView.as_view(), name="api-mismatch-scan-run"),
    path("releases/<int:release_item_id>/mismatches", ReleaseMismatchListAPIView.as_view(), name="api-release-mismatch-list"),
    path("vendor-actions/<int:action_id>/status", VendorActionStatusAPIView.as_view(), name="api-vendor-action-status"),
    path("audit-events", AuditEventListAPIView.as_view(), name="api-audit-events"),
    path("ado/sprint-snapshots/import", ADOSprintSnapshotImportAPIView.as_view(), name="api-ado-sprint-import"),
]
