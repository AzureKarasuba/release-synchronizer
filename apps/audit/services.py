import json
from uuid import UUID, uuid4

from django.core.serializers.json import DjangoJSONEncoder

from apps.audit.context import get_request_id
from apps.audit.models import AuditEvent


def _to_jsonable(payload: dict) -> dict:
    return json.loads(json.dumps(payload, cls=DjangoJSONEncoder))


def create_audit_event(*, actor, action: str, entity, change_reason: str, before_data: dict, after_data: dict, source: str):
    request_id = get_request_id()
    request_uuid = uuid4()
    if request_id:
        try:
            request_uuid = UUID(str(request_id))
        except ValueError:
            request_uuid = uuid4()

    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity_type=entity._meta.label_lower,
        entity_id=str(entity.pk),
        change_reason=change_reason,
        before_data=_to_jsonable(before_data or {}),
        after_data=_to_jsonable(after_data or {}),
        source=source,
        request_id=request_uuid,
    )
