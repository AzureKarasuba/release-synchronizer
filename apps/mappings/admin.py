from django.contrib import admin

from apps.mappings.models import ReleaseSprintMapping


@admin.register(ReleaseSprintMapping)
class ReleaseSprintMappingAdmin(admin.ModelAdmin):
    list_display = ("release_item", "sprint_snapshot", "mapping_source", "created_by", "created_at")
    list_filter = ("mapping_source",)
    search_fields = ("release_item__title", "sprint_snapshot__sprint_name", "sprint_snapshot__external_sprint_id")
