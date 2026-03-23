from django.db import transaction
from django.forms.models import model_to_dict
from django.utils import timezone

from apps.approvals.models import CostApproval
from apps.audit.services import create_audit_event
from apps.releases.models import ReleaseItem, ReleasePlan


@transaction.atomic
def create_release_plan(*, actor, **plan_data) -> ReleasePlan:
    release_plan = ReleasePlan.objects.create(**plan_data)
    create_audit_event(
        actor=actor,
        action="release_plan.created",
        entity=release_plan,
        change_reason="Release plan created",
        before_data={},
        after_data=model_to_dict(release_plan),
        source="ui",
    )
    return release_plan


@transaction.atomic
def update_release_plan(*, release_plan: ReleasePlan, actor, change_reason: str, **updates) -> ReleasePlan:
    before_data = model_to_dict(release_plan)
    for field_name, value in updates.items():
        setattr(release_plan, field_name, value)
    release_plan.save()
    create_audit_event(
        actor=actor,
        action="release_plan.updated",
        entity=release_plan,
        change_reason=change_reason,
        before_data=before_data,
        after_data=model_to_dict(release_plan),
        source="ui",
    )
    return release_plan


@transaction.atomic
def create_release_item(*, actor, change_reason: str, **item_data) -> ReleaseItem:
    release_item = ReleaseItem.objects.create(**item_data)

    if release_item.cost_estimate:
        CostApproval.objects.get_or_create(release_item=release_item)

    create_audit_event(
        actor=actor,
        action="release_item.created",
        entity=release_item,
        change_reason=change_reason,
        before_data={},
        after_data=model_to_dict(release_item),
        source="ui",
    )
    return release_item


@transaction.atomic
def update_release_item(*, release_item: ReleaseItem, actor, change_reason: str, **updates) -> ReleaseItem:
    before_data = model_to_dict(release_item)
    for field_name, value in updates.items():
        setattr(release_item, field_name, value)

    if updates.get("manual_override"):
        release_item.override_updated_by = actor
        release_item.override_updated_at = timezone.now()

    release_item.save()

    if release_item.cost_estimate and not hasattr(release_item, "cost_approval"):
        CostApproval.objects.create(release_item=release_item)

    create_audit_event(
        actor=actor,
        action="release_item.updated",
        entity=release_item,
        change_reason=change_reason,
        before_data=before_data,
        after_data=model_to_dict(release_item),
        source="ui",
    )
    return release_item
