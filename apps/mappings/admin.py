from django.contrib import admin

from apps.mappings.models import ManualTicketAssignment, ReleaseSprintMapping


@admin.register(ReleaseSprintMapping)
class ReleaseSprintMappingAdmin(admin.ModelAdmin):
    list_display = ("release_item", "sprint_snapshot", "mapping_source", "created_by", "created_at")
    list_filter = ("mapping_source",)
    search_fields = ("release_item__title", "sprint_snapshot__sprint_name", "sprint_snapshot__external_sprint_id")


@admin.register(ManualTicketAssignment)
class ManualTicketAssignmentAdmin(admin.ModelAdmin):
    list_display = ("work_item", "release_plan", "assignment_mode", "updated_by", "updated_at")
    list_filter = ("assignment_mode",)
    search_fields = ("work_item__work_item_id", "work_item__title", "release_plan__code", "release_plan__name")
