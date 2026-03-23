from django.contrib import admin

from apps.releases.models import ReleaseItem, ReleasePlan


@admin.register(ReleasePlan)
class ReleasePlanAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "business_unit",
        "status",
        "is_auto_generated",
        "default_azure_iteration_path",
        "target_start_date",
        "target_end_date",
    )
    search_fields = ("code", "name", "business_unit", "default_azure_iteration_path")
    list_filter = ("status", "business_unit", "is_auto_generated")


@admin.register(ReleaseItem)
class ReleaseItemAdmin(admin.ModelAdmin):
    list_display = ("title", "release_plan", "status", "target_release_date", "manual_override")
    search_fields = ("title", "release_plan__code", "release_plan__name")
    list_filter = ("status", "manual_override", "currency")
