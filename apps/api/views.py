import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import CanImportSprintSnapshots, CanManageMismatch, CanManageVendorActions, HasInternalStaffRole
from apps.api.serializers import ADOSprintImportSerializer, AuditEventSerializer, MismatchFindingSerializer, VendorActionStatusUpdateSerializer
from apps.common.constants import RoleType
from apps.common.permissions import user_has_role
from apps.integrations.models import ADOSprintSnapshot
from apps.mismatch.models import MismatchFinding
from apps.mismatch.services import scan_release_item_mismatches
from apps.releases.models import ReleaseItem
from apps.audit.models import AuditEvent
from apps.vendor_queue.models import VendorAction
from apps.vendor_queue.services import update_vendor_action_status


class RunMismatchScanAPIView(APIView):
    permission_classes = [CanManageMismatch]

    def post(self, request):
        scanned = 0
        for item in ReleaseItem.objects.all().iterator():
            scan_release_item_mismatches(item)
            scanned += 1
        return Response({"scanned_release_items": scanned}, status=status.HTTP_200_OK)


class ReleaseMismatchListAPIView(APIView):
    permission_classes = [HasInternalStaffRole]

    def get(self, request, release_item_id: int):
        findings = MismatchFinding.objects.filter(release_item_id=release_item_id).order_by("status", "-detected_at")
        serializer = MismatchFindingSerializer(findings, many=True)
        return Response(serializer.data)


class VendorActionStatusAPIView(APIView):
    permission_classes = [CanManageVendorActions]

    def post(self, request, action_id: int):
        serializer = VendorActionStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_action = get_object_or_404(VendorAction, pk=action_id)

        # Vendor users are restricted to actions explicitly assigned to them.
        if user_has_role(request.user, RoleType.VENDOR_USER) and vendor_action.owner_id != request.user.id:
            raise PermissionDenied("You can only update vendor actions assigned to you.")

        updated = update_vendor_action_status(
            vendor_action=vendor_action,
            actor=request.user,
            new_status=serializer.validated_data["status"],
            note=serializer.validated_data.get("note", ""),
        )
        return Response({"id": updated.id, "status": updated.status})


class AuditEventListAPIView(APIView):
    permission_classes = [HasInternalStaffRole]

    def get(self, request):
        queryset = AuditEvent.objects.all()
        entity_type = request.query_params.get("entity_type")
        entity_id = request.query_params.get("entity_id")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        serializer = AuditEventSerializer(queryset[:200], many=True)
        return Response(serializer.data)


class ADOSprintSnapshotImportAPIView(APIView):
    permission_classes = [CanImportSprintSnapshots]

    def post(self, request):
        serializer = ADOSprintImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        batch_id = uuid.uuid4()
        source_project = serializer.validated_data["source_project"]
        rows = serializer.validated_data["rows"]

        created = []
        for row in rows:
            created.append(
                ADOSprintSnapshot.objects.create(
                    snapshot_batch_id=batch_id,
                    source_project=source_project,
                    external_sprint_id=row["external_sprint_id"],
                    sprint_name=row["sprint_name"],
                    iteration_path=row.get("iteration_path", ""),
                    start_date=row.get("start_date"),
                    end_date=row.get("end_date"),
                    state=row.get("state", ""),
                )
            )

        return Response(
            {
                "snapshot_batch_id": str(batch_id),
                "source_project": source_project,
                "imported_count": len(created),
            },
            status=status.HTTP_201_CREATED,
        )
