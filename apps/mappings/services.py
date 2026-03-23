from django.forms.models import model_to_dict

from apps.audit.services import create_audit_event
from apps.mappings.models import ReleaseSprintMapping


def create_mapping(*, release_item, sprint_snapshot, actor, notes: str = "") -> tuple[ReleaseSprintMapping, bool]:
    mapping, created = ReleaseSprintMapping.objects.get_or_create(
        release_item=release_item,
        sprint_snapshot=sprint_snapshot,
        defaults={
            "mapping_source": "manual",
            "notes": notes,
            "created_by": actor if getattr(actor, "is_authenticated", False) else None,
        },
    )

    if created:
        create_audit_event(
            actor=actor,
            action="mapping.created",
            entity=mapping,
            change_reason=notes or "Manual mapping created",
            before_data={},
            after_data=model_to_dict(mapping),
            source="ui",
        )

    return mapping, created
