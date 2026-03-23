import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import RoleAssignment
from apps.common.constants import RoleType
from apps.common.permissions import can_view_cost, is_internal_staff


@pytest.mark.django_db
def test_can_view_cost_only_for_designated_roles():
    user_model = get_user_model()
    finance = user_model.objects.create_user(username="finance_u")
    engineer = user_model.objects.create_user(username="eng_u")

    RoleAssignment.objects.create(user=finance, role=RoleType.FINANCE_APPROVER, is_active=True)
    RoleAssignment.objects.create(user=engineer, role=RoleType.ENGINEERING_LEAD, is_active=True)

    assert can_view_cost(finance) is True
    assert can_view_cost(engineer) is False


@pytest.mark.django_db
def test_vendor_user_not_internal_staff():
    user_model = get_user_model()
    vendor = user_model.objects.create_user(username="vendor_u")

    RoleAssignment.objects.create(user=vendor, role=RoleType.VENDOR_USER, is_active=True)

    assert is_internal_staff(vendor) is False
