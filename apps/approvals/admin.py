from django.contrib import admin

from apps.approvals.models import CostApproval


@admin.register(CostApproval)
class CostApprovalAdmin(admin.ModelAdmin):
    list_display = ("release_item", "status", "approver", "approval_date", "updated_at")
    list_filter = ("status",)
    search_fields = ("release_item__title", "release_item__release_plan__code")
