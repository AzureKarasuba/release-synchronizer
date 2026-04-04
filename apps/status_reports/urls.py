from django.urls import path

from apps.status_reports.views import (
    StatusReportListView,
    create_status_report_item,
    delete_status_report_item,
    request_status_report_subscription,
    update_status_report_item,
    verify_status_report_subscription,
)

urlpatterns = [
    path("", StatusReportListView.as_view(), name="status-report"),
    path("create/", create_status_report_item, name="status-report-create"),
    path("<int:item_id>/update/", update_status_report_item, name="status-report-update"),
    path("<int:item_id>/delete/", delete_status_report_item, name="status-report-delete"),
    path("subscribe/", request_status_report_subscription, name="status-report-subscribe"),
    path("verify/<uuid:token>/", verify_status_report_subscription, name="status-report-verify"),
]
