from datetime import timedelta

from django.utils import timezone

from apps.approvals.models import CostApprovalStatus
from apps.mismatch.models import FindingSeverity, FindingStatus, FindingType, MismatchFinding
from apps.releases.models import ReleaseItem
from apps.vendor_queue.models import VendorActionStatus


def scan_release_item_mismatches(release_item: ReleaseItem) -> list[MismatchFinding]:
    now = timezone.now()
    findings = []

    # Missing approval for items with a cost estimate.
    cost_approval = getattr(release_item, "cost_approval", None)
    if release_item.cost_estimate and (not cost_approval or cost_approval.status != CostApprovalStatus.APPROVED):
        findings.append(
            _upsert_finding(
                fingerprint=f"missing_approval:{release_item.id}",
                finding_type=FindingType.MISSING_APPROVAL,
                severity=FindingSeverity.HIGH,
                release_item=release_item,
                vendor_action=None,
                now=now,
                details={"reason": "Cost estimate exists but approval is not approved."},
            )
        )

    # Unmapped release item.
    if not release_item.sprint_mappings.exists():
        findings.append(
            _upsert_finding(
                fingerprint=f"unmapped_release_item:{release_item.id}",
                finding_type=FindingType.UNMAPPED_RELEASE_ITEM,
                severity=FindingSeverity.MEDIUM,
                release_item=release_item,
                vendor_action=None,
                now=now,
                details={"reason": "Release item has no sprint mapping."},
            )
        )

    # Stale vendor updates.
    open_vendor_actions = release_item.vendor_actions.exclude(status=VendorActionStatus.DONE)
    for action in open_vendor_actions:
        if not action.last_vendor_update_at:
            is_stale = True
        else:
            threshold = action.last_vendor_update_at + timedelta(days=action.stale_after_days)
            is_stale = threshold < now

        if is_stale:
            findings.append(
                _upsert_finding(
                    fingerprint=f"stale_vendor_update:{action.id}",
                    finding_type=FindingType.STALE_VENDOR_UPDATE,
                    severity=FindingSeverity.MEDIUM,
                    release_item=release_item,
                    vendor_action=action,
                    now=now,
                    details={
                        "reason": "Vendor action has no recent update.",
                        "stale_after_days": action.stale_after_days,
                    },
                )
            )

    _resolve_missing_findings(release_item=release_item, active_fingerprints={f.fingerprint for f in findings}, now=now)
    return findings


def _upsert_finding(*, fingerprint, finding_type, severity, release_item, vendor_action, now, details):
    finding, created = MismatchFinding.objects.get_or_create(
        fingerprint=fingerprint,
        defaults={
            "finding_type": finding_type,
            "severity": severity,
            "status": FindingStatus.OPEN,
            "release_item": release_item,
            "vendor_action": vendor_action,
            "details": details,
            "detected_at": now,
            "last_checked_at": now,
        },
    )

    if not created:
        finding.finding_type = finding_type
        finding.severity = severity
        finding.details = details
        finding.last_checked_at = now
        if finding.status in {FindingStatus.RESOLVED, FindingStatus.IGNORED}:
            finding.status = FindingStatus.OPEN
            finding.resolved_at = None
            finding.resolution_note = ""
            finding.resolved_by = None
        finding.save(update_fields=["finding_type", "severity", "details", "last_checked_at", "status", "resolved_at", "resolution_note", "resolved_by", "updated_at"])
    return finding


def _resolve_missing_findings(*, release_item, active_fingerprints: set[str], now):
    stale_open_findings = MismatchFinding.objects.filter(release_item=release_item).exclude(
        fingerprint__in=active_fingerprints,
    ).exclude(status__in=[FindingStatus.RESOLVED, FindingStatus.IGNORED])

    for finding in stale_open_findings:
        finding.status = FindingStatus.RESOLVED
        finding.resolved_at = now
        finding.resolution_note = "Resolved automatically by mismatch scan"
        finding.last_checked_at = now
        finding.save(update_fields=["status", "resolved_at", "resolution_note", "last_checked_at", "updated_at"])
