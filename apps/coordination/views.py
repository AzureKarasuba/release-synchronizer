from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin, user_has_any_role
from apps.coordination.services import (
    assign_story_to_release,
    get_effective_release_for_story,
    get_manual_diff_rows,
    reset_story_assignment_to_azure,
)
from apps.integrations.models import ADOUserStory
from apps.integrations.services import apply_story_to_azure_iteration, get_story_sync_state, sync_ado_everything
from apps.mappings.models import ManualAssignmentMode
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
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stories = (
            ADOUserStory.objects.filter(is_active=True)
            .select_related("manual_assignment__release_plan")
            .order_by("sprint_name", "target_date", "work_item_id")
        )

        grouped: dict[str, list] = {}
        for story in stories:
            grouped.setdefault(story.sprint_name or "Unassigned", []).append(story)

        context["stories_by_sprint"] = grouped
        context["sync_state"] = get_story_sync_state()
        context["can_trigger_sync"] = user_has_any_role(self.request.user, EDITOR_ROLES)
        return context


class ManualReleaseBoardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "coordination/manual_board.html"
    allowed_roles = VIEWER_ROLES

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stories = (
            ADOUserStory.objects.filter(is_active=True)
            .select_related("manual_assignment__release_plan")
            .order_by("target_date", "work_item_id")
        )

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

        ordered_groups = sorted(grouped.values(), key=lambda g: (g["release"].is_auto_generated, g["release"].name.lower()))
        releases = list(ReleasePlan.objects.filter(status__in=["draft", "active"]).order_by("name"))

        context["release_groups"] = ordered_groups
        context["releases"] = releases
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
        context["can_apply"] = user_has_any_role(self.request.user, DIFF_ROLES)
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

    return JsonResponse({"ok": True})


@login_required
@require_POST
def reset_story_to_azure(request, story_id: int):
    if not user_has_any_role(request.user, DIFF_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    story = get_object_or_404(ADOUserStory, pk=story_id)
    reset_story_assignment_to_azure(story=story, actor=request.user, reason="Reset from diff screen")
    messages.success(request, f"Story #{story.work_item_id} reset to Azure default.")
    return redirect("diff-apply")


@login_required
@require_POST
def apply_manual_to_azure(request, story_id: int):
    if not user_has_any_role(request.user, DIFF_ROLES):
        return JsonResponse({"detail": "forbidden"}, status=403)

    story = get_object_or_404(ADOUserStory.objects.select_related("manual_assignment__release_plan"), pk=story_id)
    assignment = getattr(story, "manual_assignment", None)

    if not assignment or assignment.assignment_mode != ManualAssignmentMode.MANUAL or not assignment.release_plan_id:
        messages.error(request, "Manual assignment is required before applying to Azure.")
        return redirect("diff-apply")

    target_iteration_path = assignment.release_plan.default_azure_iteration_path
    if not target_iteration_path:
        messages.error(request, "Selected release has no Azure iteration mapping.")
        return redirect("diff-apply")

    writeback = apply_story_to_azure_iteration(story=story, target_iteration_path=target_iteration_path, actor=request.user)
    if writeback.status == "applied":
        story.sprint_path = target_iteration_path
        story.sprint_name = target_iteration_path.split("\\")[-1]
        story.save(update_fields=["sprint_path", "sprint_name", "updated_at"])
        messages.success(request, f"Applied story #{story.work_item_id} to Azure iteration '{target_iteration_path}'.")
    else:
        messages.error(request, f"Azure apply failed: {writeback.error_message}")

    return redirect("diff-apply")
