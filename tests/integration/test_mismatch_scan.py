from datetime import timedelta

import pytest
from django.utils import timezone

from apps.approvals.models import CostApproval, CostApprovalStatus
from apps.mismatch.services import scan_release_item_mismatches
from apps.releases.models import ReleaseItem, ReleasePlan
from apps.vendor_queue.models import VendorAction, VendorActionType


@pytest.mark.django_db
def test_mismatch_scan_creates_expected_findings_for_unapproved_and_unmapped_item():
    plan = ReleasePlan.objects.create(code="R-100", name="Release 100", business_unit="Core")
    release_item = ReleaseItem.objects.create(
        release_plan=plan,
        title="Data migration",
        cost_estimate=1000,
        currency="USD",
    )
    CostApproval.objects.create(release_item=release_item, status=CostApprovalStatus.PENDING)
    VendorAction.objects.create(
        release_item=release_item,
        vendor_name="VendorX",
        action_type=VendorActionType.UPDATE_ADO,
        last_vendor_update_at=timezone.now() - timedelta(days=30),
    )

    findings = scan_release_item_mismatches(release_item)

    finding_types = {f.finding_type for f in findings}
    assert "missing_approval" in finding_types
    assert "unmapped_release_item" in finding_types
    assert "stale_vendor_update" in finding_types
