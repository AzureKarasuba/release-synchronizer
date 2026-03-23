from django import forms
from django.forms import ModelForm

from apps.releases.models import ReleaseItem, ReleasePlan


class ReleasePlanForm(ModelForm):
    class Meta:
        model = ReleasePlan
        fields = [
            "code",
            "name",
            "description",
            "business_unit",
            "status",
            "target_start_date",
            "target_end_date",
            "owner",
        ]


class ReleasePlanUpdateForm(ModelForm):
    change_reason = forms.CharField(max_length=500, required=True, help_text="Required for audit traceability.")

    class Meta:
        model = ReleasePlan
        fields = [
            "code",
            "name",
            "description",
            "business_unit",
            "status",
            "target_start_date",
            "target_end_date",
            "owner",
        ]


class ReleaseItemCreateForm(ModelForm):
    change_reason = forms.CharField(max_length=500, required=True, help_text="Why is this release item being added?")

    class Meta:
        model = ReleaseItem
        fields = [
            "release_plan",
            "title",
            "description",
            "status",
            "target_release_date",
            "cost_estimate",
            "currency",
            "manual_override",
            "override_reason",
        ]


class ReleaseItemUpdateForm(ModelForm):
    change_reason = forms.CharField(max_length=500, required=True, help_text="Required for audit traceability.")

    class Meta:
        model = ReleaseItem
        fields = [
            "title",
            "description",
            "status",
            "target_release_date",
            "cost_estimate",
            "currency",
            "manual_override",
            "override_reason",
        ]
