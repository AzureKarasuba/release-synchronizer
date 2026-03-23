from django.urls import path

from apps.approvals.views import CostApprovalDetailView, CostApprovalQueueView

urlpatterns = [
    path("", CostApprovalQueueView.as_view(), name="cost-approval-queue"),
    path("<int:pk>/", CostApprovalDetailView.as_view(), name="cost-approval-detail"),
]
