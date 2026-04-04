from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.status_reports.models import ReportSubscription, StatusReportItem


def _site_base_url() -> str:
    configured = str(getattr(settings, "SITE_BASE_URL", "")).strip()
    if configured:
        return configured.rstrip("/")

    hosts = getattr(settings, "ALLOWED_HOSTS", [])
    if hosts:
        host = hosts[0]
        if host and host != "*":
            return f"https://{host}"
    return "http://127.0.0.1:8000"


def build_status_report_digest_text(items: list[StatusReportItem]) -> str:
    now_local = timezone.localtime(timezone.now())
    lines = [
        "Release Synchronizer - Daily Status Report",
        f"Generated at: {now_local.strftime('%Y-%m-%d %H:%M %Z')}",
        "",
    ]

    if not items:
        lines.append("No status report items yet.")
        return "\n".join(lines)

    for index, item in enumerate(items, start=1):
        due = item.due_date.isoformat() if item.due_date else "-"
        lines.extend(
            [
                f"{index}. {item.title}",
                f"   Owner: {item.owner_name}",
                f"   Due: {due}",
                f"   Status: {item.get_status_display()}",
                f"   Content: {item.content}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def send_subscription_verification_email(subscription: ReportSubscription) -> int:
    verify_link = f"{_site_base_url()}/status-report/verify/{subscription.verification_token}/"
    subject = "Verify your Status Report subscription"
    body = (
        "You requested daily status report emails from the Release Synchronizer demo.\n\n"
        f"Verify your email by opening this link:\n{verify_link}\n\n"
        "If you did not request this, you can ignore this message."
    )

    return send_mail(
        subject,
        body,
        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@release-synchronizer.local"),
        [subscription.email],
        fail_silently=False,
    )


def send_daily_digest() -> tuple[int, int]:
    items = list(StatusReportItem.objects.all())
    body = build_status_report_digest_text(items)
    recipients = list(
        ReportSubscription.objects.filter(is_verified=True, is_active=True).order_by("email")
    )

    sent_count = 0
    for sub in recipients:
        delivered = send_mail(
            "Daily Status Report",
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@release-synchronizer.local"),
            [sub.email],
            fail_silently=False,
        )
        if delivered:
            sub.last_sent_at = timezone.now()
            sub.save(update_fields=["last_sent_at", "updated_at"])
            sent_count += 1

    return sent_count, len(recipients)
