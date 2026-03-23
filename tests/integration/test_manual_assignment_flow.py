import pytest
from django.contrib.auth import get_user_model

from apps.coordination.services import assign_story_to_release, get_effective_release_for_story, reset_story_assignment_to_azure
from apps.integrations.models import ADOUserStory
from apps.integrations.services import ensure_auto_release_for_sprint
from apps.releases.models import ReleasePlan, ReleasePlanStatus


@pytest.mark.django_db
def test_manual_assignment_overrides_default_release_then_resets():
    user = get_user_model().objects.create_user(username="planner")
    story = ADOUserStory.objects.create(
        work_item_id=999001,
        title="Sample",
        sprint_path="Proj\\Sprint A",
        sprint_name="Sprint A",
        is_active=True,
    )

    default_release = ensure_auto_release_for_sprint(sprint_path=story.sprint_path, sprint_name=story.sprint_name)
    custom_release = ReleasePlan.objects.create(
        code="REL-CUSTOM-1",
        name="Custom Release",
        business_unit="Payments",
        status=ReleasePlanStatus.ACTIVE,
    )

    assign_story_to_release(story=story, release_plan=custom_release, actor=user, reason="Planning override")
    story.refresh_from_db()

    assert get_effective_release_for_story(story).id == custom_release.id

    reset_story_assignment_to_azure(story=story, actor=user, reason="Reset")
    story.refresh_from_db()

    assert get_effective_release_for_story(story).id == default_release.id
