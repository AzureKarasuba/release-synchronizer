from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services import assign_role
from apps.common.constants import RoleType


class Command(BaseCommand):
    help = "Assign one of the default internal roles to a user."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)
        parser.add_argument("role", choices=[choice[0] for choice in RoleType.choices])

    def handle(self, *args, **options):
        username = options["username"]
        role = options["role"]
        user_model = get_user_model()

        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist as exc:
            raise CommandError(f"User not found: {username}") from exc

        assign_role(user=user, role=role)
        self.stdout.write(self.style.SUCCESS(f"Assigned role '{role}' to '{username}'"))
