from rest_framework import serializers

from apps.audit.models import AuditEvent
from apps.mismatch.models import MismatchFinding
from apps.vendor_queue.models import VendorAction


class VendorActionStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=VendorAction._meta.get_field("status").choices)
    note = serializers.CharField(required=False, allow_blank=True)


class MismatchFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MismatchFinding
        fields = [
            "id",
            "finding_type",
            "severity",
            "status",
            "release_item_id",
            "vendor_action_id",
            "details",
            "detected_at",
            "last_checked_at",
            "resolved_at",
            "resolution_note",
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "created_at",
            "actor_id",
            "action",
            "entity_type",
            "entity_id",
            "change_reason",
            "before_data",
            "after_data",
            "source",
            "request_id",
        ]


class ADOSprintImportItemSerializer(serializers.Serializer):
    external_sprint_id = serializers.CharField(max_length=100)
    sprint_name = serializers.CharField(max_length=200)
    iteration_path = serializers.CharField(max_length=255, required=False, allow_blank=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    state = serializers.CharField(max_length=40, required=False, allow_blank=True)


class ADOSprintImportSerializer(serializers.Serializer):
    source_project = serializers.CharField(max_length=120)
    rows = ADOSprintImportItemSerializer(many=True)
