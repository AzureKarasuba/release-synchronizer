from django.forms.models import model_to_dict
from django.utils import timezone

from apps.approvals.models import CostApproval, CostApprovalStatus
from apps.audit.services import create_audit_event


def approve_cost(*, approval: CostApproval, actor, notes: str = "") -> CostApproval:
    before_data = model_to_dict(approval)
    approval.status = CostApprovalStatus.APPROVED
    approval.approver = actor
    approval.approval_date = timezone.now()
    approval.notes = notes
    approval.save()
    create_audit_event(
        actor=actor,
        action="cost_approval.approved",
        entity=approval,
        change_reason=notes or "Cost approved",
        before_data=before_data,
        after_data=model_to_dict(approval),
        source="ui",
    )
    return approval


def reject_cost(*, approval: CostApproval, actor, notes: str) -> CostApproval:
    before_data = model_to_dict(approval)
    approval.status = CostApprovalStatus.REJECTED
    approval.approver = actor
    approval.approval_date = timezone.now()
    approval.notes = notes
    approval.save()
    create_audit_event(
        actor=actor,
        action="cost_approval.rejected",
        entity=approval,
        change_reason=notes,
        before_data=before_data,
        after_data=model_to_dict(approval),
        source="ui",
    )
    return approval
