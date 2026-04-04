import pytest
from django.urls import reverse

from apps.status_reports.models import ReportSubscription, StatusReportItem


@pytest.mark.django_db
def test_status_report_item_create_without_login(client):
    response = client.post(
        reverse("status-report-create"),
        {
            "editor_name": "Demo User",
            "title": "Coordination update",
            "content": "Vendor ETA shifted by one day.",
            "owner_name": "PM",
            "status": "in_progress",
            "order_index": "10",
        },
    )

    assert response.status_code == 302
    item = StatusReportItem.objects.get(title="Coordination update")
    assert item.updated_by_display_name == "Demo User"


@pytest.mark.django_db
def test_status_report_subscription_requires_verification(client):
    subscribe_resp = client.post(
        reverse("status-report-subscribe"),
        {
            "editor_name": "Demo User",
            "email": "demo@example.com",
        },
    )
    assert subscribe_resp.status_code == 302

    sub = ReportSubscription.objects.get(email="demo@example.com")
    assert sub.is_verified is False
    assert sub.is_active is False

    verify_resp = client.get(reverse("status-report-verify", args=[sub.verification_token]))
    assert verify_resp.status_code == 302

    sub.refresh_from_db()
    assert sub.is_verified is True
    assert sub.is_active is True
