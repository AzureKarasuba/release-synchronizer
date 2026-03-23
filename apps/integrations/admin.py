from django.contrib import admin

from apps.integrations.models import ADOSprintSnapshot, ADOUserStory, AzureWritebackRequest, IntegrationSyncState


@admin.register(ADOSprintSnapshot)
class ADOSprintSnapshotAdmin(admin.ModelAdmin):
    list_display = ("source_project", "external_sprint_id", "sprint_name", "start_date", "end_date", "state")
    search_fields = ("source_project", "external_sprint_id", "sprint_name", "iteration_path")
    list_filter = ("source_project", "state")


@admin.register(ADOUserStory)
class ADOUserStoryAdmin(admin.ModelAdmin):
    list_display = ("work_item_id", "title", "state", "assigned_to", "sprint_name", "target_date", "is_active")
    search_fields = ("work_item_id", "title", "assigned_to", "sprint_name", "sprint_path")
    list_filter = ("is_active", "state", "sprint_name", "cost_approved")


@admin.register(AzureWritebackRequest)
class AzureWritebackRequestAdmin(admin.ModelAdmin):
    list_display = ("work_item", "target_iteration_path", "status", "requested_by", "processed_at", "created_at")
    search_fields = ("work_item__work_item_id", "work_item__title", "target_iteration_path")
    list_filter = ("status",)


@admin.register(IntegrationSyncState)
class IntegrationSyncStateAdmin(admin.ModelAdmin):
    list_display = ("key", "last_status", "last_synced_at", "last_batch_id")
    search_fields = ("key", "last_status")
