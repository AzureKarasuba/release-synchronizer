from django.core.management.base import BaseCommand

from apps.status_reports.services import send_daily_digest


class Command(BaseCommand):
    help = "Send daily status report email digest to verified subscribers."

    def handle(self, *args, **options):
        sent_count, recipient_count = send_daily_digest()
        self.stdout.write(
            self.style.SUCCESS(
                f"Daily status report sent to {sent_count}/{recipient_count} verified subscriber(s)."
            )
        )
