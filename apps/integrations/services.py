import base64
import json
import re
import urllib.parse
import urllib.request
import uuid
import zlib
from dataclasses import dataclass
from datetime import date, datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.integrations.models import ADOSprintSnapshot, ADOUserStory, AzureWritebackRequest, IntegrationSyncState
from apps.releases.models import ReleasePlan, ReleasePlanStatus


@dataclass
class SyncResult:
    synced: bool
    source_project: str
    imported_count: int
    batch_id: str | None
    last_synced_at: str | None
    message: str


def latest_snapshot_for_project(source_project: str):
    latest = ADOSprintSnapshot.objects.filter(source_project=source_project).order_by("-created_at").first()
    if not latest:
        return ADOSprintSnapshot.objects.none()
    return ADOSprintSnapshot.objects.filter(snapshot_batch_id=latest.snapshot_batch_id).order_by("start_date", "sprint_name")


def sync_ado_everything(*, force: bool = False) -> dict:
    sprint_result = sync_ado_sprints(force=force)
    story_result = sync_ado_user_stories(force=force)
    return {
        "sprints": sprint_result,
        "stories": story_result,
    }


def sync_ado_sprints(*, force: bool = False) -> SyncResult:
    org = getattr(settings, "ADO_ORGANIZATION", "").strip()
    project = getattr(settings, "ADO_PROJECT", "").strip()
    pat = getattr(settings, "ADO_PAT", "").strip()
    interval_seconds = getattr(settings, "ADO_SYNC_INTERVAL_SECONDS", 300)

    if not org or not project or not pat:
        return SyncResult(
            synced=False,
            source_project=project or "",
            imported_count=0,
            batch_id=None,
            last_synced_at=None,
            message="ADO sprint sync skipped: set ADO_ORGANIZATION, ADO_PROJECT, and ADO_PAT.",
        )

    state, _ = IntegrationSyncState.objects.get_or_create(key=f"ado-sprints:{org}:{project}")
    now = timezone.now()

    if not force and state.last_synced_at:
        elapsed = (now - state.last_synced_at).total_seconds()
        if elapsed < interval_seconds:
            return SyncResult(
                synced=False,
                source_project=project,
                imported_count=0,
                batch_id=str(state.last_batch_id) if state.last_batch_id else None,
                last_synced_at=state.last_synced_at.isoformat(),
                message="Sprint sync skipped: interval not elapsed.",
            )

    try:
        iterations = _fetch_ado_iterations(org=org, project=project, pat=pat)
        if not iterations:
            state.last_status = "ok"
            state.last_error = ""
            state.last_synced_at = now
            state.save(update_fields=["last_status", "last_error", "last_synced_at"])
            return SyncResult(
                synced=True,
                source_project=project,
                imported_count=0,
                batch_id=None,
                last_synced_at=now.isoformat(),
                message="Sprint sync complete: no iterations returned.",
            )

        batch_id = uuid.uuid4()
        imported_count = _persist_iteration_snapshot(project=project, iterations=iterations, batch_id=batch_id)

        state.last_status = "ok"
        state.last_error = ""
        state.last_batch_id = batch_id
        state.last_synced_at = timezone.now()
        state.save(update_fields=["last_status", "last_error", "last_batch_id", "last_synced_at"])

        return SyncResult(
            synced=True,
            source_project=project,
            imported_count=imported_count,
            batch_id=str(batch_id),
            last_synced_at=state.last_synced_at.isoformat() if state.last_synced_at else None,
            message="Sprint sync complete.",
        )
    except Exception as exc:  # noqa: BLE001
        state.last_status = "error"
        state.last_error = str(exc)
        state.last_synced_at = timezone.now()
        state.save(update_fields=["last_status", "last_error", "last_synced_at"])
        return SyncResult(
            synced=False,
            source_project=project,
            imported_count=0,
            batch_id=None,
            last_synced_at=state.last_synced_at.isoformat() if state.last_synced_at else None,
            message=f"Sprint sync failed: {exc}",
        )


def sync_ado_user_stories(*, force: bool = False) -> SyncResult:
    org = getattr(settings, "ADO_ORGANIZATION", "").strip()
    project = getattr(settings, "ADO_PROJECT", "").strip()
    pat = getattr(settings, "ADO_PAT", "").strip()
    interval_seconds = getattr(settings, "ADO_SYNC_INTERVAL_SECONDS", 300)

    if not org or not project or not pat:
        return SyncResult(
            synced=False,
            source_project=project or "",
            imported_count=0,
            batch_id=None,
            last_synced_at=None,
            message="ADO story sync skipped: set ADO_ORGANIZATION, ADO_PROJECT, and ADO_PAT.",
        )

    state, _ = IntegrationSyncState.objects.get_or_create(key=f"ado-stories:{org}:{project}")
    now = timezone.now()

    if not force and state.last_synced_at:
        elapsed = (now - state.last_synced_at).total_seconds()
        if elapsed < interval_seconds:
            return SyncResult(
                synced=False,
                source_project=project,
                imported_count=0,
                batch_id=str(state.last_batch_id) if state.last_batch_id else None,
                last_synced_at=state.last_synced_at.isoformat(),
                message="Story sync skipped: interval not elapsed.",
            )

    try:
        ids = _fetch_story_ids(org=org, project=project, pat=pat)
        stories = _fetch_work_items_batch(org=org, project=project, pat=pat, ids=ids) if ids else []

        batch_id = uuid.uuid4()
        imported_count = _persist_story_snapshot(stories=stories, synced_at=now)

        state.last_status = "ok"
        state.last_error = ""
        state.last_batch_id = batch_id
        state.last_synced_at = timezone.now()
        state.save(update_fields=["last_status", "last_error", "last_batch_id", "last_synced_at"])

        return SyncResult(
            synced=True,
            source_project=project,
            imported_count=imported_count,
            batch_id=str(batch_id),
            last_synced_at=state.last_synced_at.isoformat() if state.last_synced_at else None,
            message="Story sync complete.",
        )
    except Exception as exc:  # noqa: BLE001
        state.last_status = "error"
        state.last_error = str(exc)
        state.last_synced_at = timezone.now()
        state.save(update_fields=["last_status", "last_error", "last_synced_at"])
        return SyncResult(
            synced=False,
            source_project=project,
            imported_count=0,
            batch_id=None,
            last_synced_at=state.last_synced_at.isoformat() if state.last_synced_at else None,
            message=f"Story sync failed: {exc}",
        )


def get_story_sync_state() -> IntegrationSyncState | None:
    org = getattr(settings, "ADO_ORGANIZATION", "").strip()
    project = getattr(settings, "ADO_PROJECT", "").strip()
    if not org or not project:
        return None
    return IntegrationSyncState.objects.filter(key=f"ado-stories:{org}:{project}").first()


def apply_story_to_azure_iteration(*, story: ADOUserStory, target_iteration_path: str, actor=None) -> AzureWritebackRequest:
    request_row = AzureWritebackRequest.objects.create(
        work_item=story,
        target_iteration_path=target_iteration_path,
        status=AzureWritebackRequest.Status.PENDING,
        requested_by=actor if getattr(actor, "is_authenticated", False) else None,
    )

    org = getattr(settings, "ADO_ORGANIZATION", "").strip()
    project = getattr(settings, "ADO_PROJECT", "").strip()
    pat = getattr(settings, "ADO_PAT", "").strip()

    if not org or not project or not pat:
        request_row.status = AzureWritebackRequest.Status.FAILED
        request_row.error_message = "Missing ADO credentials in settings."
        request_row.processed_at = timezone.now()
        request_row.save(update_fields=["status", "error_message", "processed_at", "updated_at"])
        return request_row

    try:
        _patch_story_iteration(
            org=org,
            project=project,
            pat=pat,
            work_item_id=story.work_item_id,
            iteration_path=target_iteration_path,
        )
        request_row.status = AzureWritebackRequest.Status.APPLIED
        request_row.error_message = ""
        request_row.processed_at = timezone.now()
        request_row.save(update_fields=["status", "error_message", "processed_at", "updated_at"])
    except Exception as exc:  # noqa: BLE001
        request_row.status = AzureWritebackRequest.Status.FAILED
        request_row.error_message = str(exc)
        request_row.processed_at = timezone.now()
        request_row.save(update_fields=["status", "error_message", "processed_at", "updated_at"])

    return request_row


def _fetch_ado_iterations(*, org: str, project: str, pat: str) -> list[dict]:
    org_encoded = urllib.parse.quote(org)
    project_encoded = urllib.parse.quote(project)
    url = (
        f"https://dev.azure.com/{org_encoded}/{project_encoded}"
        "/_apis/wit/classificationnodes/iterations"
        "?$depth=10&api-version=7.1-preview.2"
    )

    payload = _request_json(url=url, pat=pat, method="GET")
    root = payload or {}
    items: list[dict] = []
    _walk_iteration_tree(root, items)
    return items


def _fetch_story_ids(*, org: str, project: str, pat: str) -> list[int]:
    org_encoded = urllib.parse.quote(org)
    project_encoded = urllib.parse.quote(project)
    url = f"https://dev.azure.com/{org_encoded}/{project_encoded}/_apis/wit/wiql?api-version=7.1-preview.2"

    wiql = {
        "query": (
            "SELECT [System.Id] FROM WorkItems "
            "WHERE [System.TeamProject] = @project "
            "AND [System.WorkItemType] = 'User Story' "
            "AND [System.State] <> 'Removed' "
            "ORDER BY [System.ChangedDate] DESC"
        )
    }
    payload = _request_json(url=url, pat=pat, method="POST", body=wiql)
    work_items = payload.get("workItems") or []
    return [int(row["id"]) for row in work_items if row.get("id")]


def _fetch_work_items_batch(*, org: str, project: str, pat: str, ids: list[int]) -> list[dict]:
    if not ids:
        return []

    org_encoded = urllib.parse.quote(org)
    project_encoded = urllib.parse.quote(project)
    url = f"https://dev.azure.com/{org_encoded}/{project_encoded}/_apis/wit/workitemsbatch?api-version=7.1-preview.1"

    fields = [
        "System.Id",
        "System.Title",
        "System.AssignedTo",
        "System.State",
        "System.IterationPath",
        "System.ChangedDate",
        "Microsoft.VSTS.Scheduling.TargetDate",
    ]

    rows: list[dict] = []
    chunk_size = 200
    for start in range(0, len(ids), chunk_size):
        chunk = ids[start : start + chunk_size]
        body = {"ids": chunk, "fields": fields}
        payload = _request_json(url=url, pat=pat, method="POST", body=body)
        rows.extend(payload.get("value") or [])

    return rows


def _patch_story_iteration(*, org: str, project: str, pat: str, work_item_id: int, iteration_path: str):
    org_encoded = urllib.parse.quote(org)
    project_encoded = urllib.parse.quote(project)
    url = (
        f"https://dev.azure.com/{org_encoded}/{project_encoded}"
        f"/_apis/wit/workitems/{work_item_id}?api-version=7.1-preview.3"
    )

    token = base64.b64encode(f":{pat}".encode("utf-8")).decode("ascii")
    body = [{"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path}]
    data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, method="PATCH")
    request.add_header("Authorization", f"Basic {token}")
    request.add_header("Accept", "application/json")
    request.add_header("Content-Type", "application/json-patch+json")

    with urllib.request.urlopen(request, timeout=30):
        return


def _request_json(*, url: str, pat: str, method: str = "GET", body: dict | None = None) -> dict:
    token = base64.b64encode(f":{pat}".encode("utf-8")).decode("ascii")
    data = json.dumps(body).encode("utf-8") if body is not None else None

    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Basic {token}")
    request.add_header("Accept", "application/json")
    if body is not None:
        request.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")

    return json.loads(raw) if raw else {}


def _walk_iteration_tree(node: dict, items: list[dict]):
    children = node.get("children") or []
    if not children:
        path = node.get("path") or node.get("name")
        if path:
            attrs = node.get("attributes") or {}
            items.append(
                {
                    "external_sprint_id": str(node.get("identifier") or path),
                    "sprint_name": node.get("name") or path,
                    "iteration_path": path,
                    "start_date": _parse_iso_date(attrs.get("startDate")),
                    "end_date": _parse_iso_date(attrs.get("finishDate")),
                    "state": _derive_state(attrs.get("startDate"), attrs.get("finishDate")),
                }
            )
        return

    for child in children:
        _walk_iteration_tree(child, items)


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    date_part = value.split("T", 1)[0]
    return date.fromisoformat(date_part)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _derive_state(start_raw: str | None, end_raw: str | None) -> str:
    today = timezone.now().date()
    start_date = _parse_iso_date(start_raw)
    end_date = _parse_iso_date(end_raw)

    if start_date and today < start_date:
        return "future"
    if start_date and end_date and start_date <= today <= end_date:
        return "active"
    if end_date and today > end_date:
        return "closed"
    return "unknown"


def _extract_assigned_to(raw_assigned) -> str:
    if raw_assigned is None:
        return ""
    if isinstance(raw_assigned, dict):
        return raw_assigned.get("displayName") or raw_assigned.get("uniqueName") or ""
    return str(raw_assigned)


def _extract_sprint_name(sprint_path: str) -> str:
    if not sprint_path:
        return "Unassigned"
    return sprint_path.split("\\")[-1]


def _normalize_release_code_from_sprint(sprint_path: str) -> str:
    if not sprint_path:
        sprint_path = "UNASSIGNED"
    suffix = zlib.crc32(sprint_path.encode("utf-8")) % 100000000
    return f"AUTO-{suffix}"


@transaction.atomic
def _persist_iteration_snapshot(*, project: str, iterations: list[dict], batch_id: uuid.UUID) -> int:
    created = 0
    for row in iterations:
        ADOSprintSnapshot.objects.create(
            snapshot_batch_id=batch_id,
            source_project=project,
            external_sprint_id=row["external_sprint_id"],
            sprint_name=row["sprint_name"],
            iteration_path=row.get("iteration_path", ""),
            start_date=row.get("start_date"),
            end_date=row.get("end_date"),
            state=row.get("state", ""),
        )
        created += 1
    return created


@transaction.atomic
def _persist_story_snapshot(*, stories: list[dict], synced_at) -> int:
    seen_ids: set[int] = set()
    imported = 0

    for row in stories:
        work_item_id = int(row["id"])
        fields = row.get("fields") or {}

        title = str(fields.get("System.Title") or "")
        assigned_to = _extract_assigned_to(fields.get("System.AssignedTo"))
        state = str(fields.get("System.State") or "")
        sprint_path = str(fields.get("System.IterationPath") or "")
        sprint_name = _extract_sprint_name(sprint_path)
        target_date = _parse_iso_date(fields.get("Microsoft.VSTS.Scheduling.TargetDate"))
        changed_date = _parse_iso_datetime(fields.get("System.ChangedDate"))
        azure_url = str((((row.get("_links") or {}).get("html") or {}).get("href") or ""))

        story, created = ADOUserStory.objects.get_or_create(
            work_item_id=work_item_id,
            defaults={
                "title": title,
                "assigned_to": assigned_to,
                "state": state,
                "sprint_path": sprint_path,
                "sprint_name": sprint_name,
                "target_date": target_date,
                "changed_date": changed_date,
                "azure_url": azure_url,
                "is_active": True,
                "last_synced_at": synced_at,
                "raw_fields": fields,
            },
        )

        if not created:
            story.title = title
            story.assigned_to = assigned_to
            story.state = state
            story.sprint_path = sprint_path
            story.sprint_name = sprint_name
            story.target_date = target_date
            story.changed_date = changed_date
            story.azure_url = azure_url
            story.is_active = True
            story.last_synced_at = synced_at
            story.raw_fields = fields
            story.save(
                update_fields=[
                    "title",
                    "assigned_to",
                    "state",
                    "sprint_path",
                    "sprint_name",
                    "target_date",
                    "changed_date",
                    "azure_url",
                    "is_active",
                    "last_synced_at",
                    "raw_fields",
                    "updated_at",
                ]
            )

        ensure_auto_release_for_sprint(sprint_path=sprint_path, sprint_name=sprint_name)
        seen_ids.add(work_item_id)
        imported += 1

    if seen_ids:
        ADOUserStory.objects.exclude(work_item_id__in=seen_ids).filter(is_active=True).update(is_active=False, last_synced_at=synced_at)

    return imported


def ensure_auto_release_for_sprint(*, sprint_path: str, sprint_name: str) -> ReleasePlan:
    code = _normalize_release_code_from_sprint(sprint_path)
    release, created = ReleasePlan.objects.get_or_create(
        code=code,
        defaults={
            "name": sprint_name or code,
            "description": "Auto-generated from Azure sprint classification.",
            "business_unit": "AUTO_FROM_AZURE",
            "status": ReleasePlanStatus.ACTIVE,
            "is_auto_generated": True,
            "default_azure_iteration_path": sprint_path,
        },
    )

    if not created:
        dirty = False
        if release.is_auto_generated is False:
            release.is_auto_generated = True
            dirty = True
        if sprint_name and release.name != sprint_name:
            release.name = sprint_name
            dirty = True
        if sprint_path and release.default_azure_iteration_path != sprint_path:
            release.default_azure_iteration_path = sprint_path
            dirty = True
        if dirty:
            release.save(update_fields=["is_auto_generated", "name", "default_azure_iteration_path", "updated_at"])

    return release


def compact_release_code_hint(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return cleaned[:32] if cleaned else "RELEASE"
