from apps.integrations.models import ADOSprintSnapshot


def latest_snapshot_for_project(source_project: str):
    latest = ADOSprintSnapshot.objects.filter(source_project=source_project).order_by("-created_at").first()
    if not latest:
        return ADOSprintSnapshot.objects.none()
    return ADOSprintSnapshot.objects.filter(snapshot_batch_id=latest.snapshot_batch_id).order_by("start_date", "sprint_name")
