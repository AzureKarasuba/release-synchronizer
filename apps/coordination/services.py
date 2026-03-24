from collections import OrderedDict

from django.db import transaction

from apps.audit.services import create_audit_event
from apps.integrations.models import ADOUserStory
from apps.integrations.services import ensure_auto_release_for_sprint
from apps.mappings.models import ManualAssignmentMode, ManualTicketAssignment
from apps.releases.models import ReleasePlan


def get_default_release_for_story(story: ADOUserStory) -> ReleasePlan:
    return ensure_auto_release_for_sprint(sprint_path=story.sprint_path, sprint_name=story.sprint_name)


def get_effective_release_for_story(story: ADOUserStory) -> ReleasePlan:
    assignment = getattr(story, "manual_assignment", None)
    if assignment and assignment.assignment_mode == ManualAssignmentMode.MANUAL and assignment.release_plan_id:
        return assignment.release_plan
    return get_default_release_for_story(story)


def build_story_hierarchy_blocks(stories):
    grouped = OrderedDict()

    for story in stories:
        parent_id = story.parent_work_item_id
        if parent_id:
            key = f"parent-{parent_id}"
            if key not in grouped:
                grouped[key] = {
                    "parent": {
                        "work_item_id": parent_id,
                        "title": story.parent_title or "(Untitled Parent)",
                        "type": story.parent_work_item_type or "Parent",
                    },
                    "stories": [],
                }
            grouped[key]["stories"].append(story)
        else:
            key = f"story-{story.id}"
            grouped[key] = {
                "parent": None,
                "stories": [story],
            }

    return list(grouped.values())


@transaction.atomic
def assign_story_to_release(*, story: ADOUserStory, release_plan: ReleasePlan, actor, reason: str = "") -> ManualTicketAssignment:
    assignment, _ = ManualTicketAssignment.objects.get_or_create(work_item=story)
    before = {
        "assignment_mode": assignment.assignment_mode,
        "release_plan_id": assignment.release_plan_id,
        "override_reason": assignment.override_reason,
    }

    assignment.assignment_mode = ManualAssignmentMode.MANUAL
    assignment.release_plan = release_plan
    assignment.override_reason = reason
    assignment.updated_by = actor if getattr(actor, "is_authenticated", False) else None
    assignment.save()

    create_audit_event(
        actor=actor,
        action="manual_assignment.updated",
        entity=assignment,
        change_reason=reason or "Manual release assignment updated",
        before_data=before,
        after_data={
            "assignment_mode": assignment.assignment_mode,
            "release_plan_id": assignment.release_plan_id,
            "override_reason": assignment.override_reason,
        },
        source="ui",
    )

    return assignment


@transaction.atomic
def reset_story_assignment_to_azure(*, story: ADOUserStory, actor, reason: str = "") -> ManualTicketAssignment:
    assignment, _ = ManualTicketAssignment.objects.get_or_create(work_item=story)
    before = {
        "assignment_mode": assignment.assignment_mode,
        "release_plan_id": assignment.release_plan_id,
        "override_reason": assignment.override_reason,
    }

    assignment.assignment_mode = ManualAssignmentMode.AZURE_DEFAULT
    assignment.release_plan = None
    assignment.override_reason = ""
    assignment.updated_by = actor if getattr(actor, "is_authenticated", False) else None
    assignment.save()

    create_audit_event(
        actor=actor,
        action="manual_assignment.reset_to_azure",
        entity=assignment,
        change_reason=reason or "Reset to Azure default",
        before_data=before,
        after_data={
            "assignment_mode": assignment.assignment_mode,
            "release_plan_id": assignment.release_plan_id,
            "override_reason": assignment.override_reason,
        },
        source="ui",
    )

    return assignment


def get_manual_diff_rows(*, stories):
    rows = []
    for story in stories:
        assignment = getattr(story, "manual_assignment", None)
        if not assignment or assignment.assignment_mode != ManualAssignmentMode.MANUAL or not assignment.release_plan_id:
            continue

        azure_release = get_default_release_for_story(story)
        manual_release = assignment.release_plan

        # If manual release maps to same Azure iteration path, this is not a mismatch.
        if manual_release.default_azure_iteration_path and manual_release.default_azure_iteration_path == story.sprint_path:
            continue

        if manual_release.id == azure_release.id:
            continue

        rows.append(
            {
                "story": story,
                "azure_release": azure_release,
                "manual_release": manual_release,
                "assignment": assignment,
            }
        )

    return rows
