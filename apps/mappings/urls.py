from django.urls import path

from apps.mappings.views import MappingCreateView, MappingListView

urlpatterns = [
    path("", MappingListView.as_view(), name="mapping-list"),
    path("new/", MappingCreateView.as_view(), name="mapping-create"),
]
