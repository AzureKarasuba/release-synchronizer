from django import forms

from apps.vendor_queue.models import VendorAction


class VendorActionStatusForm(forms.Form):
    status = forms.ChoiceField(choices=VendorAction._meta.get_field("status").choices)
    note = forms.CharField(widget=forms.Textarea, required=False)
