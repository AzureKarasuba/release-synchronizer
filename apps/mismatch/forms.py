from django import forms

from apps.mismatch.models import FindingStatus, MismatchFinding


class MismatchTriageForm(forms.Form):
    status = forms.ChoiceField(choices=MismatchFinding._meta.get_field("status").choices)
    resolution_note = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        note = (cleaned_data.get("resolution_note") or "").strip()
        if status in {FindingStatus.RESOLVED, FindingStatus.IGNORED} and not note:
            self.add_error("resolution_note", "Resolution note is required when resolving or ignoring.")
        return cleaned_data
