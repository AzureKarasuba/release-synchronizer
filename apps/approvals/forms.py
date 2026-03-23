from django import forms

from apps.approvals.models import CostApproval, CostApprovalStatus


class CostApprovalDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[
            (CostApprovalStatus.APPROVED, "Approve"),
            (CostApprovalStatus.REJECTED, "Reject"),
        ]
    )
    notes = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get("decision")
        notes = (cleaned_data.get("notes") or "").strip()
        if decision == CostApprovalStatus.REJECTED and not notes:
            self.add_error("notes", "Notes are required when rejecting.")
        return cleaned_data


class CostApprovalInlineForm(forms.ModelForm):
    class Meta:
        model = CostApproval
        fields = ["notes"]
