from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.services import assign_role
from apps.approvals.models import CostApproval, CostApprovalStatus
from apps.common.constants import RoleType
from apps.integrations.models import ADOSprintSnapshot
from apps.mappings.models import ReleaseSprintMapping
from apps.mismatch.services import scan_release_item_mismatches
from apps.releases.models import ReleaseItem, ReleasePlan, ReleasePlanStatus
from apps.vendor_queue.models import VendorAction, VendorActionStatus, VendorActionType


class Command(BaseCommand):
    help = "Seed demo data for Release Synchronizer prototype."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="ChangeMe123!", help="Default password for created demo users")

    def handle(self, *args, **options):
        password = options["password"]
        user_model = get_user_model()

        users = {
            "rm_demo": RoleType.RELEASE_MANAGER,
            "eng_demo": RoleType.ENGINEERING_LEAD,
            "fin_demo": RoleType.FINANCE_APPROVER,
            "vc_demo": RoleType.VENDOR_COORDINATOR,
            "vendor_demo": RoleType.VENDOR_USER,
            "exec_demo": RoleType.EXECUTIVE_VIEWER,
        }

        created_users = {}
        for username, role in users.items():
            user, created = user_model.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.local"},
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
            assign_role(user=user, role=role)
            created_users[username] = user

        plan, _ = ReleasePlan.objects.get_or_create(
            code="REL-2026-Q2-A",
            defaults={
                "name": "Q2 Checkout Expansion",
                "description": "Business release plan for checkout expansion and phased vendor rollout.",
                "business_unit": "Payments",
                "status": ReleasePlanStatus.ACTIVE,
                "target_start_date": date.today(),
                "target_end_date": date.today() + timedelta(days=45),
                "owner": created_users["rm_demo"],
            },
        )

        item_a, _ = ReleaseItem.objects.get_or_create(
            release_plan=plan,
            title="Gateway Routing Rules",
            defaults={
                "description": "Manual release plan item controlling routing changes by region.",
                "status": "in_progress",
                "target_release_date": date.today() + timedelta(days=20),
                "cost_estimate": Decimal("12000.00"),
                "currency": "USD",
                "manual_override": True,
                "override_reason": "Adjusted release window to align with partner launch",
                "override_updated_by": created_users["rm_demo"],
                "override_updated_at": timezone.now(),
            },
        )

        item_b, _ = ReleaseItem.objects.get_or_create(
            release_plan=plan,
            title="Fraud Rule Bundle",
            defaults={
                "description": "Risk policy updates from security working group.",
                "status": "planned",
                "target_release_date": date.today() + timedelta(days=30),
                "cost_estimate": Decimal("5000.00"),
                "currency": "USD",
            },
        )

        approval_a, _ = CostApproval.objects.get_or_create(release_item=item_a)
        approval_a.status = CostApprovalStatus.APPROVED
        approval_a.approver = created_users["fin_demo"]
        approval_a.approval_date = timezone.now() - timedelta(days=2)
        approval_a.notes = "Approved with quarterly budget carryover"
        approval_a.save()

        approval_b, _ = CostApproval.objects.get_or_create(release_item=item_b)
        approval_b.status = CostApprovalStatus.PENDING
        approval_b.notes = "Awaiting vendor revised estimate"
        approval_b.save()

        batch_id = UUID("00000000-0000-0000-0000-000000000001")
        snapshot_1, _ = ADOSprintSnapshot.objects.get_or_create(
            snapshot_batch_id=batch_id,
            external_sprint_id="SPR-501",
            defaults={
                "source_project": "PaymentsCore",
                "sprint_name": "Sprint 50.1",
                "iteration_path": "PaymentsCore\\ReleaseTrain\\Sprint 50.1",
                "start_date": date.today() - timedelta(days=5),
                "end_date": date.today() + timedelta(days=9),
                "state": "active",
            },
        )

        snapshot_2, _ = ADOSprintSnapshot.objects.get_or_create(
            snapshot_batch_id=batch_id,
            external_sprint_id="SPR-502",
            defaults={
                "source_project": "PaymentsCore",
                "sprint_name": "Sprint 50.2",
                "iteration_path": "PaymentsCore\\ReleaseTrain\\Sprint 50.2",
                "start_date": date.today() + timedelta(days=10),
                "end_date": date.today() + timedelta(days=24),
                "state": "future",
            },
        )

        ReleaseSprintMapping.objects.get_or_create(
            release_item=item_a,
            sprint_snapshot=snapshot_1,
            defaults={
                "mapping_source": "manual",
                "notes": "Primary implementation sprint",
                "created_by": created_users["eng_demo"],
            },
        )
        ReleaseSprintMapping.objects.get_or_create(
            release_item=item_a,
            sprint_snapshot=snapshot_2,
            defaults={
                "mapping_source": "manual",
                "notes": "Carry-over hardening tasks",
                "created_by": created_users["eng_demo"],
            },
        )

        vendor_action, _ = VendorAction.objects.get_or_create(
            release_item=item_b,
            vendor_name="Contoso Vendor Ops",
            action_type=VendorActionType.UPDATE_ADO,
            defaults={
                "status": VendorActionStatus.OPEN,
                "due_date": date.today() + timedelta(days=3),
                "owner": created_users["vendor_demo"],
                "last_vendor_update_at": timezone.now() - timedelta(days=12),
                "stale_after_days": 7,
                "notes": "Vendor to update ADO tasks after approval",
            },
        )

        scan_release_item_mismatches(item_a)
        scan_release_item_mismatches(item_b)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
        self.stdout.write("Demo users:")
        for username, role in users.items():
            self.stdout.write(f"- {username} ({role})")
        self.stdout.write(f"Default password: {password}")
        self.stdout.write(f"Created/updated vendor action id: {vendor_action.id}")
