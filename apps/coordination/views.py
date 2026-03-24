import csv
import urllib.parse
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.audit.services import create_audit_event
from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin, user_has_any_role
from apps.coordination.services import (
    assign_story_to_release,
    build_story_hierarchy_blocks,
    get_effective_release_for_story,
    get_manual_diff_rows,
    reset_story_assignment_to_azure,
)
from apps.integrations.models import ADOSprintSnapshot, ADOUserStory
from apps.integrations.services import compact_release_code_hint, get_story_sync_state, sync_ado_everything
from apps.mappings.models import ManualAssignmentMode, ManualTicketAssignment
from apps.releases.models import ReleasePlan


VIEWER_ROLES = (
    RoleType.RELEASE_MANAGER,
    RoleType.ENGINEERING_LEAD,
    RoleType.FINANCE_APPROVER,
    RoleType.VENDOR_COORDINATOR,
    RoleType.EXECUTIVE_VIEWER,
    RoleType.SYSTEM_ADMIN,
)

EDITOR_ROLES = {
    RoleType.RELEASE_MANAGER,
    RoleType.ENGINEERING_LEAD,
    RoleType.VENDOR_COORDINATOR,
    RoleType.SYSTEM_ADMIN,
}

DIFF_ROLES = {
    RoleType.RELEASE_MANAGER,
    RoleType.ENGINEERING_LEAD,
    RoleType.SYSTEM_ADMIN,
}


def _default_story_link(work_item_id: int) -> str:
    org = getattr(settings, "ADO_ORGANIZATION", "").strip()
    project = getattr(settings, "ADO_PROJECT", "").strip()
    if not org or not project:
        return ""
    return (
        f"https://dev.azure.com/{urllib.parse.quote(org)}/{urllib.parse.quote(project)}"
        f"/_workitems/edit/{work_item_id}"
    )


def _sprint_span_map_for_current_project() -> dict[str, dict]:
    project = getattr(settings, "ADO_PROJECT", "").strip()
    if not project:
        return {}

    latest = ADOSprintSnapshot.objects.filter(source_project=project).order_by("-created_at").first()
    if not latest:
        return {}

    rows = ADOSprintSnapshot.objects.filter(snapshot_batch_id=latest.snapshot_batch_id)
    result: dict[str, dict] = {}
    for row in rows:
        result[row.sprint_name] = {
            "start_date": row.start_date,
            "end_date": row.end_date,
        }
    return result


def _active_stories_with_links(*, order_fields: tuple[str, ...]) -> list[ADOUserStory]:
    stories = list(
        ADOUserStory.objects.filter(is_active=True)
        .select_related("manual_assignment__release_plan")
        .order_by(*order_fields)
    )
    for story in stories:
        story.display_url = story.azure_url or _default_story_link(story.work_item_id)
    return stories


def _build_mirror_groups(stories: list[ADOUserStory], span_map: dict[str, dict]) -> dict[str, dict]:
    grouped_raw: dict[str, list] = {}
    for story in stories:
        grouped_raw.setdefault(story.sprint_name or "Unassigned", []).append(story)

    grouped: dict[str, dict] = {}
    for sprint_name, sprint_stories in grouped_raw.items():
        grouped[sprint_name] = {
            "count": len(sprint_stories),
            "blocks": build_story_hierarchy_blocks(sprint_stories),
            "span": span_map.get(sprint_name),
        }
    return grouped


def _build_manual_groups(stories: list[ADOUserStory]) -> tuple[list[dict], list[dict]]:
    grouped: dict[int, dict] = {}
    for story in stories:
        release = get_effective_release_for_story(story)
        bucket = grouped.setdefault(
            release.id,
            {
                "release": release,
                "stories": [],
            },
        )
        bucket["stories"].append(story)

    all_releases = list(
        ReleasePlan.objects.filter(status__in=["draft", "active"]).order_by("is_auto_generated", "name", "id")
    )
    for release in all_releases:
        grouped.setdefault(
            release.id,
            {
                "release": release,
                "stories": [],
            },
        )

    release_label_by_id = {release.id: f"Release {idx}" for idx, release in enumerate(all_releases, start=1)}

    ordered_groups = sorted(grouped.values(), key=lambda g: (g["release"].is_auto_generated, g["release"].name.lower()))
    for idx, group in enumerate(ordered_groups, start=1):
        group["release_label"] = release_label_by_id.get(group["release"].id, f"Release {idx}")
        group["story_blocks"] = build_story_hierarchy_blocks(group["stories"])
        group["release_date_value"] = group["release"].target_end_date.isoformat() if group["release"].target_end_date else ""

    release_options = [
        {
            "id": release.id,
            "label": release_label_by_id.get(release.id, release.name),
            "code": release.code,
        }
        for release in all_releases
    ]
    return ordered_groups, release_options


def _generate_manual_release_code(name: str) -> str:
    base_hint = compact_release_code_hint(name or "RELEASE")
    if not base_hint.startswith("MANUAL-"):
        base_hint = f"MANUAL-{base_hint}"
    base_hint = base_hint[:40]

    candidate = base_hint
    seq = 2
    while ReleasePlan.objects.filter(code=candidate).exists():
        suffix = f"-{seq}"
        candidate = f"{base_hint[: max(1, 40 - len(suffix))]}{suffix}"
        seq += 1
    return candidate


def _default_manual_release_name() -> str:
    return f"Manual Release {ReleasePlan.objects.filter(is_auto_generated=False).count() + 1}"

def _csv_response(filename: str) -> tuple[HttpResponse, csv.writer]:
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    return response, writer


def _export_mirror_csv(stories: list[ADOUserStory], span_map: dict[str, dict]) -> HttpResponse:
    response, writer = _csv_response("azure_mirror.csv")
    writer.writerow(
        [
            "ticket_id",
            "title",
            "story_points",
            "parent_ticket_id",
            "parent_title",
            "parent_type",
            "assigned_to",
            "state",
            "sprint",
            "sprint_start_date",
            "sprint_end_date",
            "target_date",
            "cost_approved",
            "cost_approved_at",
            "ticket_url",
        ]
    )

    for story in stories:
        span = span_map.get(story.sprint_name or "", {})
        writer.writerow(
            [
                story.work_item_id,
                story.title,
                story.story_points,
                story.parent_work_item_id,
                story.parent_title,
                story.parent_work_item_type,
                story.assigned_to,
                story.state,
                story.sprint_name,
                span.get("start_date"),
                span.get("end_date"),
                story.target_date,
                story.cost_approved,
                story.cost_approved_at,
                story.display_url,
            ]
        )

    return response


def _export_manual_csv(groups: list[dict]) -> HttpResponse:
    response, writer = _csv_response("manual_release_plan.csv")
    writer.writerow(
        [
            "release_label",
            "release_code",
            "release_date",
            "ticket_id",
            "title",
            "story_points",
            "parent_ticket_id",
            "parent_title",
            "parent_type",
            "assigned_to",
            "state",
            "source_sprint",
            "target_date",
            "ticket_url",
        ]
    )

    for group in groups:
        for block in group["story_blocks"]:
            for story in block["stories"]:
                writer.writerow(
                    [
                        group["release_label"],
                        group["release"].code,
                        group["release"].target_end_date,
                        story.work_item_id,
                        story.title,
                        story.story_points,
                        story.parent_work_item_id,
                        story.parent_title,
                        story.parent_work_item_type,
                        story.assigned_to,
                        story.state,
                        story.sprint_name,
                        story.target_date,
                        story.display_url,
                    ]
                )

    return response


class AzureMirrorView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "coordination/azure_mirror.html"
    allowed_roles = VIEWER_ROLES

    def get(self, request, *args, **kwargs):
        if request.GET.get("sync") == "1" and user_has_any_role(request.user, EDITOR_ROLES):
            result = sync_ado_everything(force=True)
            messages.info(
                request,
                f"Sync finished. Stories imported: {result['stories'].imported_count}, Sprints imported: {result['sprints'].imported_count}",
            )
            return redirect("azure-mirror")

        if request.GET.get("export") == "csv":
            stories = _active_stories_with_links(order_fields=("sprint_name", "parent_work_item_id", "target_date", "work_item_id"))
            span_map = _sprint_span_map_for_current_project()
            return _export_mirror_csv(stories=stories, span_map=span_map)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stories = _active_stories_with_links(order_fields=("sprint_name", "parent_work_item_id", "target_date", "work_item_id"))
        span_map = _sprint_span_map_for_current_project()

        context["stories_by_sprint"] = _build_mirror_groups(stories=stories, span_map=span_map)
        context["sync_state"] = get_story_sync_state()
        context["can_trigger_sync"] = user_has_any_role(self.request.user, EDITOR_ROLES)
        return context


class ManualReleaseBoardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "coordination/manual_board.html"
    allowed_roles = VIEWER_ROLES

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            stories = _active_stories_with_links(order_fields=("parent_work_item_id", "target_date", "work_item_id"))
            groups, _ = _build_manual_groups(stories=stories)
            return _export_manual_csv(groups=groups)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stories = _active_stories_with_links(order_fields=("parent_work_item_id", "target_date", "work_item_id"))

        groups, release_options = _build_manual_groups(stories=stories)
        context["release_groups"] = groups
        context["release_options"] = release_options
        context["can_edit"] = user_has_any_role(self.request.user, EDITOR_ROLES)
        return context


class DiffApplyView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "coordination/diff_apply.html"
    allowed_roles = VIEWER_ROLES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stories = (
            ADOUserStory.objects.filter(is_active=True)
            .select_related("manual_assignment__release_plan")
            .order_by("work_item_id")
        )
        context["rows"] = get_manual_diff_rows(stories=stories)
        context["can_edit_diff"] = user_has_any_role(self.request.user, DIFF_ROLES)
        return context


@login_required
@require_POST
def move_story_to_release(request):
    if not user_has_any_role(request.user, EDITOR_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    story_id = request.POST.get("story_id")
    release_id = request.POST.get("release_id")
    reason = (request.POST.get("reason") or "").strip()
    if not story_id or not release_id:
        return HttpResponseBadRequest("story_id and release_id are required")

    story = get_object_or_404(ADOUserStory, pk=story_id)
    release = get_object_or_404(ReleasePlan, pk=release_id)
    assign_story_to_release(story=story, release_plan=release, actor=request.user, reason=reason)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})

    messages.success(request, f"Moved story #{story.work_item_id} to {release.name}.")
    return redirect("manual-board")


@login_required
@require_POST
def bulk_move_stories_to_release(request):
    if not user_has_any_role(request.user, EDITOR_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    release_id = request.POST.get("release_id")
    story_ids = request.POST.getlist("story_ids")
    reason = (request.POST.get("reason") or "").strip() or "Bulk moved via manual release table"

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not release_id:
        if is_ajax:
            return JsonResponse({"detail": "release_id is required"}, status=400)
        messages.error(request, "Please choose a destination release.")
        return redirect("manual-board")

    if not story_ids:
        if is_ajax:
            return JsonResponse({"detail": "story_ids is required"}, status=400)
        messages.error(request, "Please select at least one ticket to move.")
        return redirect("manual-board")

    release = get_object_or_404(ReleasePlan, pk=release_id)
    stories = list(ADOUserStory.objects.filter(pk__in=story_ids, is_active=True))

    moved = 0
    for story in stories:
        assign_story_to_release(story=story, release_plan=release, actor=request.user, reason=reason)
        moved += 1

    if is_ajax:
        return JsonResponse({"ok": True, "moved": moved, "release": release.name})

    messages.success(request, f"Moved {moved} ticket(s) to {release.name}.")
    return redirect("manual-board")


@login_required
@require_POST
def create_manual_release(request):
    if not user_has_any_role(request.user, EDITOR_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    raw_name = (request.POST.get("name") or "").strip()
    raw_target_end = (request.POST.get("target_end_date") or "").strip()

    release_name = raw_name or _default_manual_release_name()
    try:
        target_end_date = date.fromisoformat(raw_target_end) if raw_target_end else None
    except ValueError:
        messages.error(request, "Invalid release date format.")
        return redirect("manual-board")

    release = ReleasePlan.objects.create(
        code=_generate_manual_release_code(release_name),
        name=release_name,
        description="Manual release created from coordination board.",
        business_unit="MANUAL_COORDINATION",
        status="active",
        target_end_date=target_end_date,
        is_auto_generated=False,
    )

    create_audit_event(
        actor=request.user,
        action="release_plan.created",
        entity=release,
        change_reason="Created from manual coordination board",
        before_data={},
        after_data={
            "code": release.code,
            "name": release.name,
            "status": release.status,
            "target_end_date": release.target_end_date,
            "is_auto_generated": release.is_auto_generated,
        },
        source="ui",
    )

    messages.success(request, f"Created release {release.name} ({release.code}).")
    return redirect("manual-board")


@login_required
@require_POST
def delete_manual_release(request, release_id: int):
    if not user_has_any_role(request.user, EDITOR_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    release = get_object_or_404(ReleasePlan, pk=release_id)

    if release.is_auto_generated:
        messages.error(request, "Azure-backed releases cannot be deleted.")
        return redirect("manual-board")


    linked_item_count = release.items.count()

    reset_count = 0
    assignments = ManualTicketAssignment.objects.filter(
        release_plan=release,
        assignment_mode=ManualAssignmentMode.MANUAL,
    ).select_related("work_item")

    for assignment in assignments:
        reset_story_assignment_to_azure(
            story=assignment.work_item,
            actor=request.user,
            reason=f"Release deleted: {release.name}",
        )
        reset_count += 1

    before_data = {
        "code": release.code,
        "name": release.name,
        "status": release.status,
        "target_end_date": release.target_end_date,
        "is_auto_generated": release.is_auto_generated,
    }

    release_name = release.name
    release.delete()

    create_audit_event(
        actor=request.user,
        action="release_plan.deleted",
        entity=release,
        change_reason="Deleted from manual coordination board",
        before_data=before_data,
        after_data={
            "deleted": True,
            "reset_story_count": reset_count,
            "deleted_release_item_count": linked_item_count,
        },
        source="ui",
    )

    messages.success(
        request,
        f"Deleted {release_name}. Reset {reset_count} ticket(s) to Azure default and removed {linked_item_count} linked release item(s).",
    )
    return redirect("manual-board")

@login_required
@require_POST
def update_release_target_date(request, release_id: int):
    if not user_has_any_role(request.user, EDITOR_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    release = get_object_or_404(ReleasePlan, pk=release_id)
    raw = (request.POST.get("target_end_date") or "").strip()

    try:
        new_date = date.fromisoformat(raw) if raw else None
    except ValueError:
        messages.error(request, f"Invalid date format for {release.name}.")
        return redirect("manual-board")

    before = {"target_end_date": release.target_end_date}
    release.target_end_date = new_date
    release.save(update_fields=["target_end_date", "updated_at"])

    create_audit_event(
        actor=request.user,
        action="release_plan.target_date.updated",
        entity=release,
        change_reason="Manual release date update",
        before_data=before,
        after_data={"target_end_date": release.target_end_date},
        source="ui",
    )

    messages.success(request, f"Updated release date for {release.name}.")
    return redirect("manual-board")


@login_required
@require_POST
def reset_story_to_azure(request, story_id: int):
    if not user_has_any_role(request.user, DIFF_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    story = get_object_or_404(ADOUserStory, pk=story_id)
    reset_story_assignment_to_azure(story=story, actor=request.user, reason="Reset from diff screen")
    messages.success(request, f"Story #{story.work_item_id} reset to Azure default.")
    return redirect("diff-apply")







