import uuid

from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.audit.services import create_audit_event
from apps.status_reports.forms import ReportSubscriptionForm, StatusReportItemForm
from apps.status_reports.models import ReportSubscription, StatusReportItem
from apps.status_reports.services import send_subscription_verification_email


def _resolve_editor_name(request) -> str:
    raw = (request.POST.get("editor_name") or request.session.get("demo_editor_name") or "").strip()
    if not raw:
        return "Anonymous"
    value = raw[:120]
    request.session["demo_editor_name"] = value
    return value


class StatusReportListView(TemplateView):
    template_name = "status_reports/status_report_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = StatusReportItem.objects.all()
        context["item_form"] = StatusReportItemForm()
        context["subscription_form"] = ReportSubscriptionForm()
        context["subscriber_count"] = ReportSubscription.objects.filter(is_verified=True, is_active=True).count()
        context["demo_editor_name"] = self.request.session.get("demo_editor_name", "")
        return context


@require_POST
def create_status_report_item(request):
    form = StatusReportItemForm(request.POST)
    editor_name = _resolve_editor_name(request)

    if not form.is_valid():
        messages.error(request, "Failed to create item. Please check required fields.")
        return redirect("status-report")

    item = form.save(commit=False)
    item.updated_by_display_name = editor_name
    item.save()

    create_audit_event(
        actor=request.user,
        action="status_report.item.created",
        entity=item,
        change_reason="Created from status report page",
        before_data={},
        after_data={
            "title": item.title,
            "owner_name": item.owner_name,
            "status": item.status,
            "due_date": item.due_date,
            "updated_by_display_name": item.updated_by_display_name,
        },
        source="ui",
    )

    messages.success(request, "Status report item created.")
    return redirect("status-report")


@require_POST
def update_status_report_item(request, item_id: int):
    item = get_object_or_404(StatusReportItem, pk=item_id)
    form = StatusReportItemForm(request.POST, instance=item)
    editor_name = _resolve_editor_name(request)

    if not form.is_valid():
        messages.error(request, f"Failed to update item: {item.title}")
        return redirect("status-report")

    before_data = {
        "title": item.title,
        "content": item.content,
        "owner_name": item.owner_name,
        "status": item.status,
        "due_date": item.due_date,
        "order_index": item.order_index,
        "updated_by_display_name": item.updated_by_display_name,
    }

    updated = form.save(commit=False)
    updated.updated_by_display_name = editor_name
    updated.save()

    create_audit_event(
        actor=request.user,
        action="status_report.item.updated",
        entity=updated,
        change_reason="Updated from status report page",
        before_data=before_data,
        after_data={
            "title": updated.title,
            "content": updated.content,
            "owner_name": updated.owner_name,
            "status": updated.status,
            "due_date": updated.due_date,
            "order_index": updated.order_index,
            "updated_by_display_name": updated.updated_by_display_name,
        },
        source="ui",
    )

    messages.success(request, "Status report item updated.")
    return redirect("status-report")


@require_POST
def delete_status_report_item(request, item_id: int):
    editor_name = _resolve_editor_name(request)
    item = get_object_or_404(StatusReportItem, pk=item_id)
    before_data = {
        "title": item.title,
        "content": item.content,
        "owner_name": item.owner_name,
        "status": item.status,
        "due_date": item.due_date,
        "order_index": item.order_index,
        "updated_by_display_name": item.updated_by_display_name,
    }
    title = item.title
    item.delete()

    create_audit_event(
        actor=request.user,
        action="status_report.item.deleted",
        entity=item,
        change_reason="Deleted from status report page",
        before_data=before_data,
        after_data={"deleted": True, "title": title, "deleted_by_display_name": editor_name},
        source="ui",
    )

    messages.success(request, f"Deleted item: {title}")
    return redirect("status-report")


@require_POST
def request_status_report_subscription(request):
    form = ReportSubscriptionForm(request.POST)
    editor_name = _resolve_editor_name(request)

    if not form.is_valid():
        return HttpResponseBadRequest("email is required")

    email = str(form.cleaned_data["email"]).strip().lower()

    subscription, created = ReportSubscription.objects.get_or_create(
        email=email,
        defaults={
            "requested_by_display_name": editor_name,
            "is_active": False,
            "is_verified": False,
        },
    )

    if not created and subscription.is_verified and subscription.is_active:
        messages.info(request, "This email is already subscribed.")
        return redirect("status-report")

    before_data = {
        "is_verified": subscription.is_verified,
        "is_active": subscription.is_active,
    }

    subscription.is_verified = False
    subscription.is_active = False
    subscription.verification_token = uuid.uuid4()
    subscription.requested_by_display_name = editor_name
    subscription.save(
        update_fields=[
            "is_verified",
            "is_active",
            "verification_token",
            "requested_by_display_name",
            "updated_at",
        ]
    )

    create_audit_event(
        actor=request.user,
        action="status_report.subscription.requested",
        entity=subscription,
        change_reason="Subscription requested",
        before_data=before_data,
        after_data={
            "email": subscription.email,
            "is_verified": subscription.is_verified,
            "is_active": subscription.is_active,
            "requested_by_display_name": subscription.requested_by_display_name,
        },
        source="ui",
    )

    try:
        send_subscription_verification_email(subscription)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f"Failed to send verification email: {exc}")
        return redirect("status-report")

    messages.success(request, "Verification email sent. Please confirm before receiving daily reports.")
    return redirect("status-report")


def verify_status_report_subscription(request, token):
    subscription = get_object_or_404(ReportSubscription, verification_token=token)

    if subscription.is_verified and subscription.is_active:
        messages.info(request, "This subscription is already verified.")
        return redirect("status-report")

    before_data = {
        "is_verified": subscription.is_verified,
        "is_active": subscription.is_active,
    }

    subscription.is_verified = True
    subscription.is_active = True
    subscription.verified_at = timezone.now()
    subscription.save(update_fields=["is_verified", "is_active", "verified_at", "updated_at"])

    create_audit_event(
        actor=request.user,
        action="status_report.subscription.verified",
        entity=subscription,
        change_reason="Subscription email verified",
        before_data=before_data,
        after_data={
            "email": subscription.email,
            "is_verified": subscription.is_verified,
            "is_active": subscription.is_active,
            "verified_at": subscription.verified_at,
        },
        source="ui",
    )

    messages.success(request, "Email verified. You will receive the daily status report.")
    return redirect("status-report")
