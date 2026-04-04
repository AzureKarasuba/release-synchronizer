from django import forms

from apps.status_reports.models import ReportSubscription, StatusReportItem


class StatusReportItemForm(forms.ModelForm):
    class Meta:
        model = StatusReportItem
        fields = ["title", "content", "due_date", "owner_name", "status", "order_index"]


class ReportSubscriptionForm(forms.ModelForm):
    class Meta:
        model = ReportSubscription
        fields = ["email"]
