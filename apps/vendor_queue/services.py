from django.forms.models import model_to_dict
from django.utils import timezone

from apps.audit.services import create_audit_event
from apps.vendor_queue.models import VendorAction, VendorActionStatus


def update_vendor_action_status(*, vendor_action: VendorAction, actor, new_status: str, note: str = "") -> VendorAction:
    before_data = model_to_dict(vendor_action)
    vendor_action.status = new_status
    if new_status == VendorActionStatus.DONE:
        vendor_action.last_vendor_update_at = timezone.now()
    if note:
        vendor_action.notes = f"{vendor_action.notes}\n{note}".strip()
    vendor_action.save()
    create_audit_event(
        actor=actor,
        action="vendor_action.status_updated",
        entity=vendor_action,
        change_reason=note or f"Status changed to {new_status}",
        before_data=before_data,
        after_data=model_to_dict(vendor_action),
        source="ui",
    )
    return vendor_action
