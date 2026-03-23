from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView

from apps.approvals.forms import CostApprovalDecisionForm
from apps.approvals.models import CostApproval
from apps.approvals.services import approve_cost, reject_cost
from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin


class CostApprovalQueueView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "approvals/cost_approval_queue.html"
    model = CostApproval
    context_object_name = "approvals"
    allowed_roles = (
        RoleType.FINANCE_APPROVER,
        RoleType.RELEASE_MANAGER,
        RoleType.SYSTEM_ADMIN,
    )


class CostApprovalDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    template_name = "approvals/cost_approval_detail.html"
    model = CostApproval
    context_object_name = "approval"
    allowed_roles = CostApprovalQueueView.allowed_roles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CostApprovalDecisionForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CostApprovalDecisionForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        decision = form.cleaned_data["decision"]
        notes = form.cleaned_data.get("notes", "")
        if decision == "approved":
            approve_cost(approval=self.object, actor=request.user, notes=notes)
            messages.success(request, "Cost approval approved.")
        else:
            reject_cost(approval=self.object, actor=request.user, notes=notes)
            messages.success(request, "Cost approval rejected.")

        return redirect("cost-approval-detail", pk=self.object.pk)
