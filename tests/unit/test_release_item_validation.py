import pytest
from django.core.exceptions import ValidationError

from apps.releases.models import ReleaseItem, ReleasePlan


@pytest.mark.django_db
def test_release_item_requires_override_reason_when_manual_override():
    plan = ReleasePlan.objects.create(code="R-001", name="Release 1", business_unit="Payments")
    item = ReleaseItem(
        release_plan=plan,
        title="Cutover",
        manual_override=True,
        override_reason="",
    )

    with pytest.raises(ValidationError):
        item.save()
