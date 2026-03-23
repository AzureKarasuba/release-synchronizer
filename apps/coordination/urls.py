from django.urls import path

from apps.coordination.views import (
    AzureMirrorView,
    DiffApplyView,
    ManualReleaseBoardView,
    apply_manual_to_azure,
    move_story_to_release,
    reset_story_to_azure,
)

urlpatterns = [
    path("", AzureMirrorView.as_view(), name="azure-mirror"),
    path("mirror/", AzureMirrorView.as_view(), name="azure-mirror-alt"),
    path("manual/", ManualReleaseBoardView.as_view(), name="manual-board"),
    path("manual/move/", move_story_to_release, name="manual-move-story"),
    path("diff/", DiffApplyView.as_view(), name="diff-apply"),
    path("diff/<int:story_id>/reset/", reset_story_to_azure, name="diff-reset-story"),
    path("diff/<int:story_id>/apply/", apply_manual_to_azure, name="diff-apply-story"),
]
