from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView

from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin, user_has_role
from apps.vendor_queue.forms import VendorActionStatusForm
from apps.vendor_queue.models import VendorAction
from apps.vendor_queue.services import update_vendor_action_status


class VendorActionQueueView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "vendor_queue/vendor_action_queue.html"
    model = VendorAction
    context_object_name = "vendor_actions"
    allowed_roles = (
        RoleType.VENDOR_COORDINATOR,
        RoleType.VENDOR_USER,
        RoleType.RELEASE_MANAGER,
        RoleType.SYSTEM_ADMIN,
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        # Vendor users only see actions explicitly assigned to them.
        if user_has_role(user, RoleType.VENDOR_USER):
            return queryset.filter(owner=user)
        return queryset


class VendorActionDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    template_name = "vendor_queue/vendor_action_detail.html"
    model = VendorAction
    context_object_name = "vendor_action"
    allowed_roles = VendorActionQueueView.allowed_roles

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user_has_role(user, RoleType.VENDOR_USER):
            return queryset.filter(owner=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = VendorActionStatusForm(initial={"status": self.object.status})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VendorActionStatusForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        update_vendor_action_status(
            vendor_action=self.object,
            actor=request.user,
            new_status=form.cleaned_data["status"],
            note=form.cleaned_data.get("note", ""),
        )
        messages.success(request, "Vendor action updated.")
        return redirect("vendor-action-detail", pk=self.object.pk)
