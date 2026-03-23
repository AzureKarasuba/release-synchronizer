from django.contrib import admin

from apps.vendor_queue.models import VendorAction


@admin.register(VendorAction)
class VendorActionAdmin(admin.ModelAdmin):
    list_display = ("vendor_name", "action_type", "status", "due_date", "release_item")
    list_filter = ("status", "action_type", "vendor_name")
    search_fields = ("vendor_name", "release_item__title", "vendor_contact_email")
