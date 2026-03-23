from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.audit.models import AuditEvent
from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin, can_view_cost, user_has_any_role
from apps.releases.forms import ReleaseItemCreateForm, ReleaseItemUpdateForm, ReleasePlanForm, ReleasePlanUpdateForm
from apps.releases.models import ReleaseItem, ReleasePlan
from apps.releases.services import create_release_item, create_release_plan, update_release_item, update_release_plan


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "releases/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["release_plan_count"] = ReleasePlan.objects.count()
        context["release_item_count"] = ReleaseItem.objects.count()
        context["blocked_items_count"] = ReleaseItem.objects.filter(status="blocked").count()
        return context


class ReleasePlanListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "releases/release_plan_list.html"
    model = ReleasePlan
    context_object_name = "release_plans"
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.ENGINEERING_LEAD,
        RoleType.FINANCE_APPROVER,
        RoleType.VENDOR_COORDINATOR,
        RoleType.EXECUTIVE_VIEWER,
        RoleType.SYSTEM_ADMIN,
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_plan"] = user_has_any_role(self.request.user, {RoleType.RELEASE_MANAGER, RoleType.SYSTEM_ADMIN})
        return context


class ReleasePlanCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    template_name = "releases/release_plan_form.html"
    form_class = ReleasePlanForm
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.SYSTEM_ADMIN,
    )

    def form_valid(self, form):
        self.object = create_release_plan(actor=self.request.user, **form.cleaned_data)
        messages.success(self.request, "Release plan created.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("release-plan-detail", kwargs={"pk": self.object.pk})


class ReleasePlanDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    template_name = "releases/release_plan_detail.html"
    model = ReleasePlan
    context_object_name = "release_plan"
    allowed_roles = ReleasePlanListView.allowed_roles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_view_cost"] = can_view_cost(self.request.user)
        context["can_edit_plan"] = user_has_any_role(self.request.user, {RoleType.RELEASE_MANAGER, RoleType.SYSTEM_ADMIN})
        context["can_edit_items"] = user_has_any_role(
            self.request.user,
            {RoleType.RELEASE_MANAGER, RoleType.ENGINEERING_LEAD, RoleType.SYSTEM_ADMIN},
        )
        return context


class ReleasePlanUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    template_name = "releases/release_plan_form.html"
    form_class = ReleasePlanUpdateForm
    model = ReleasePlan
    context_object_name = "release_plan"
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.SYSTEM_ADMIN,
    )

    def form_valid(self, form):
        change_reason = form.cleaned_data.pop("change_reason")
        update_release_plan(
            release_plan=self.object,
            actor=self.request.user,
            change_reason=change_reason,
            **form.cleaned_data,
        )
        messages.success(self.request, "Release plan updated.")
        return redirect("release-plan-detail", pk=self.object.pk)


class ReleaseItemCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    template_name = "releases/release_item_form.html"
    form_class = ReleaseItemCreateForm
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.ENGINEERING_LEAD,
        RoleType.SYSTEM_ADMIN,
    )

    def get_initial(self):
        initial = super().get_initial()
        plan_id = self.kwargs.get("plan_id")
        if plan_id:
            initial["release_plan"] = get_object_or_404(ReleasePlan, pk=plan_id)
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not can_view_cost(self.request.user):
            form.fields.pop("cost_estimate", None)
            form.fields.pop("currency", None)
        return form

    def form_valid(self, form):
        change_reason = form.cleaned_data.pop("change_reason")
        create_release_item(actor=self.request.user, change_reason=change_reason, **form.cleaned_data)
        messages.success(self.request, "Release item created.")
        return redirect("release-plan-detail", pk=form.cleaned_data["release_plan"].pk)


class ReleaseItemDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    template_name = "releases/release_item_detail.html"
    model = ReleaseItem
    context_object_name = "release_item"
    allowed_roles = ReleasePlanListView.allowed_roles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_view_cost"] = can_view_cost(self.request.user)
        context["can_edit_release_item"] = user_has_any_role(
            self.request.user,
            {RoleType.RELEASE_MANAGER, RoleType.ENGINEERING_LEAD, RoleType.SYSTEM_ADMIN},
        )
        context["audit_events"] = AuditEvent.objects.filter(
            entity_type="releases.releaseitem",
            entity_id=str(self.object.pk),
        )[:50]
        return context


class ReleaseItemUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    template_name = "releases/release_item_form.html"
    form_class = ReleaseItemUpdateForm
    model = ReleaseItem
    context_object_name = "release_item"
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.ENGINEERING_LEAD,
        RoleType.SYSTEM_ADMIN,
    )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not can_view_cost(self.request.user):
            form.fields.pop("cost_estimate", None)
            form.fields.pop("currency", None)
        return form

    def form_valid(self, form):
        change_reason = form.cleaned_data.pop("change_reason")
        update_release_item(
            release_item=self.object,
            actor=self.request.user,
            change_reason=change_reason,
            **form.cleaned_data,
        )
        messages.success(self.request, "Release item updated.")
        return redirect("release-item-detail", pk=self.object.pk)
