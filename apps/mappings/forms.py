from django import forms

from apps.integrations.models import ADOSprintSnapshot
from apps.mappings.models import ReleaseSprintMapping
from apps.releases.models import ReleaseItem


class MappingCreateForm(forms.Form):
    release_item = forms.ModelChoiceField(queryset=ReleaseItem.objects.all().order_by("id"))
    sprint_snapshot = forms.ModelChoiceField(queryset=ADOSprintSnapshot.objects.all().order_by("-created_at"))
    notes = forms.CharField(widget=forms.Textarea, required=False)


class MappingUpdateForm(forms.ModelForm):
    class Meta:
        model = ReleaseSprintMapping
        fields = ["notes"]
