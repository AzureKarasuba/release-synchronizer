from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import DetailView, ListView

from apps.audit.services import create_audit_event
from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin
from apps.mismatch.forms import MismatchTriageForm
from apps.mismatch.models import FindingStatus, MismatchFinding


class MismatchListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "mismatch/mismatch_list.html"
    model = MismatchFinding
    context_object_name = "findings"
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.ENGINEERING_LEAD,
        RoleType.VENDOR_COORDINATOR,
        RoleType.SYSTEM_ADMIN,
    )


class MismatchDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    template_name = "mismatch/mismatch_detail.html"
    model = MismatchFinding
    context_object_name = "finding"
    allowed_roles = MismatchListView.allowed_roles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = MismatchTriageForm(initial={"status": self.object.status})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MismatchTriageForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        before_data = model_to_dict(self.object)
        self.object.status = form.cleaned_data["status"]
        note = form.cleaned_data.get("resolution_note", "")
        if self.object.status in {FindingStatus.RESOLVED, FindingStatus.IGNORED}:
            self.object.resolution_note = note
            self.object.resolved_by = request.user
            self.object.resolved_at = timezone.now()
        elif self.object.status == FindingStatus.IN_PROGRESS:
            self.object.resolution_note = note
            self.object.assigned_to = request.user

        self.object.save()
        create_audit_event(
            actor=request.user,
            action="mismatch.updated",
            entity=self.object,
            change_reason=note or "Mismatch triage updated",
            before_data=before_data,
            after_data=model_to_dict(self.object),
            source="ui",
        )
        messages.success(request, "Mismatch finding updated.")
        return redirect("mismatch-detail", pk=self.object.pk)
