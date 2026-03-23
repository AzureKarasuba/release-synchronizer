from django.urls import path

from apps.vendor_queue.views import VendorActionDetailView, VendorActionQueueView

urlpatterns = [
    path("", VendorActionQueueView.as_view(), name="vendor-action-queue"),
    path("<int:pk>/", VendorActionDetailView.as_view(), name="vendor-action-detail"),
]
