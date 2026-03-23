from django.contrib import admin

from apps.integrations.models import ADOSprintSnapshot


@admin.register(ADOSprintSnapshot)
class ADOSprintSnapshotAdmin(admin.ModelAdmin):
    list_display = ("source_project", "external_sprint_id", "sprint_name", "start_date", "end_date", "state")
    search_fields = ("source_project", "external_sprint_id", "sprint_name", "iteration_path")
    list_filter = ("source_project", "state")
