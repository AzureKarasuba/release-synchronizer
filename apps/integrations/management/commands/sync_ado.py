from django.core.management.base import BaseCommand

from apps.integrations.services import sync_ado_everything


class Command(BaseCommand):
    help = "Sync Azure DevOps sprints and user stories once."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force sync even if interval has not elapsed")

    def handle(self, *args, **options):
        result = sync_ado_everything(force=options.get("force", False))
        sprint = result["sprints"]
        stories = result["stories"]

        self.stdout.write(
            f"sprints: synced={sprint.synced} imported={sprint.imported_count} at={sprint.last_synced_at} msg={sprint.message}"
        )
        self.stdout.write(
            f"stories: synced={stories.synced} imported={stories.imported_count} at={stories.last_synced_at} msg={stories.message}"
        )
