from django.urls import path

from apps.mismatch.views import MismatchDetailView, MismatchListView

urlpatterns = [
    path("", MismatchListView.as_view(), name="mismatch-list"),
    path("<int:pk>/", MismatchDetailView.as_view(), name="mismatch-detail"),
]
