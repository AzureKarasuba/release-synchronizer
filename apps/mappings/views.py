from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import CreateView, ListView

from apps.common.constants import RoleType
from apps.common.permissions import RoleRequiredMixin
from apps.mappings.forms import MappingCreateForm
from apps.mappings.models import ReleaseSprintMapping
from apps.mappings.services import create_mapping


class MappingListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "mappings/mapping_list.html"
    model = ReleaseSprintMapping
    context_object_name = "mappings"
    allowed_roles = (
        RoleType.RELEASE_MANAGER,
        RoleType.ENGINEERING_LEAD,
        RoleType.SYSTEM_ADMIN,
    )


class MappingCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    template_name = "mappings/mapping_form.html"
    form_class = MappingCreateForm
    allowed_roles = MappingListView.allowed_roles

    def form_valid(self, form):
        _, created = create_mapping(
            release_item=form.cleaned_data["release_item"],
            sprint_snapshot=form.cleaned_data["sprint_snapshot"],
            actor=self.request.user,
            notes=form.cleaned_data.get("notes", ""),
        )
        if created:
            messages.success(self.request, "Release-sprint mapping created.")
        else:
            messages.info(self.request, "Mapping already exists.")
        return redirect("mapping-list")
