from django.urls import path

from apps.releases.views import (
    DashboardView,
    ReleaseItemCreateView,
    ReleaseItemDetailView,
    ReleaseItemUpdateView,
    ReleasePlanCreateView,
    ReleasePlanDetailView,
    ReleasePlanListView,
    ReleasePlanUpdateView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("release-plans/", ReleasePlanListView.as_view(), name="release-plan-list"),
    path("release-plans/new/", ReleasePlanCreateView.as_view(), name="release-plan-create"),
    path("release-plans/<int:pk>/", ReleasePlanDetailView.as_view(), name="release-plan-detail"),
    path("release-plans/<int:pk>/edit/", ReleasePlanUpdateView.as_view(), name="release-plan-update"),
    path("release-plans/<int:plan_id>/items/new/", ReleaseItemCreateView.as_view(), name="release-item-create"),
    path("release-items/<int:pk>/", ReleaseItemDetailView.as_view(), name="release-item-detail"),
    path("release-items/<int:pk>/edit/", ReleaseItemUpdateView.as_view(), name="release-item-update"),
]
