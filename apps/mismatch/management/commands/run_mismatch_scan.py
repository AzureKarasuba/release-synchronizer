from django.core.management.base import BaseCommand

from apps.mismatch.services import scan_release_item_mismatches
from apps.releases.models import ReleaseItem


class Command(BaseCommand):
    help = "Scan all release items for mismatch findings."

    def handle(self, *args, **options):
        count = 0
        for item in ReleaseItem.objects.all().iterator():
            scan_release_item_mismatches(item)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Mismatch scan complete for {count} release items."))
