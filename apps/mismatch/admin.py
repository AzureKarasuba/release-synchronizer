from django.contrib import admin

from apps.mismatch.models import MismatchFinding


@admin.register(MismatchFinding)
class MismatchFindingAdmin(admin.ModelAdmin):
    list_display = ("finding_type", "severity", "status", "release_item", "vendor_action", "detected_at")
    list_filter = ("finding_type", "severity", "status")
    search_fields = ("fingerprint", "release_item__title", "vendor_action__vendor_name")
