import csv
import uuid
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.integrations.models import ADOSprintSnapshot


class Command(BaseCommand):
    help = "Import Azure DevOps sprint snapshots from CSV."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument("--project", type=str, required=True)

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        source_project = options["project"]
        batch_id = uuid.uuid4()
        created_count = 0

        try:
            with open(csv_path, newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    ADOSprintSnapshot.objects.create(
                        snapshot_batch_id=batch_id,
                        source_project=source_project,
                        external_sprint_id=row["external_sprint_id"],
                        sprint_name=row["sprint_name"],
                        iteration_path=row.get("iteration_path", ""),
                        start_date=_parse_date(row.get("start_date")),
                        end_date=_parse_date(row.get("end_date")),
                        state=row.get("state", ""),
                    )
                    created_count += 1
        except FileNotFoundError as exc:
            raise CommandError(f"CSV not found: {csv_path}") from exc

        self.stdout.write(self.style.SUCCESS(f"Imported {created_count} sprint snapshots in batch {batch_id}"))


def _parse_date(value: str | None):
    if not value:
        return None
    return date.fromisoformat(value)
