import time

from django.core.management.base import BaseCommand

from apps.integrations.services import sync_ado_everything


class Command(BaseCommand):
    help = "Run continuous Azure DevOps sync loop every N seconds (default 300 = 5 minutes)."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=300, help="Seconds between sync attempts")

    def handle(self, *args, **options):
        interval = options["interval"]
        self.stdout.write(self.style.WARNING(f"Starting ADO sync loop every {interval}s. Ctrl+C to stop."))

        while True:
            result = sync_ado_everything(force=True)
            sprint = result["sprints"]
            stories = result["stories"]
            stamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(
                f"[{stamp}] sprints imported={sprint.imported_count} msg={sprint.message} | stories imported={stories.imported_count} msg={stories.message}"
            )
            time.sleep(interval)
