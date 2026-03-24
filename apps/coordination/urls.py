from django.urls import path

from apps.coordination.views import (
    AzureMirrorView,
    DiffApplyView,
    ManualReleaseBoardView,
    bulk_move_stories_to_release,
    create_manual_release,
    delete_manual_release,
    move_story_to_release,
    reset_story_to_azure,
    update_release_target_date,
)

urlpatterns = [
    path("", AzureMirrorView.as_view(), name="azure-mirror"),
    path("mirror/", AzureMirrorView.as_view(), name="azure-mirror-alt"),
    path("manual/", ManualReleaseBoardView.as_view(), name="manual-board"),
    path("manual/create-release/", create_manual_release, name="manual-create-release"),
    path("manual/release/<int:release_id>/delete/", delete_manual_release, name="manual-delete-release"),
    path("manual/move/", move_story_to_release, name="manual-move-story"),
    path("manual/bulk-move/", bulk_move_stories_to_release, name="manual-bulk-move-stories"),
    path("manual/release/<int:release_id>/date/", update_release_target_date, name="manual-update-release-date"),
    path("diff/", DiffApplyView.as_view(), name="diff-apply"),
    path("diff/<int:story_id>/reset/", reset_story_to_azure, name="diff-reset-story"),
]
