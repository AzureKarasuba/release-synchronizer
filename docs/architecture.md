# Architecture Notes

## Product shape
The prototype now focuses on three primary operator views:
1. Azure Mirror (strict source-aligned read view)
2. Manual Plan (release-based drag-and-drop planning)
3. Diff & Apply (compare and choose reconciliation actions)

## Data ownership
- Azure DevOps remains source-of-truth for sprint/ticket execution fields.
- Manual release placement is stored internally as overrides.
- Default manual placement mirrors Azure until a manual override is made.

## Sync model
- `sync_ado_everything()` pulls iteration hierarchy and user stories.
- A continuous worker command (`run_ado_sync_worker`) can run every 300s.
- New Azure stories are upserted and appear automatically in views.

## Apply model
- Operators can apply manual release placement back to Azure by updating `System.IterationPath`.
- Apply actions are logged in `AzureWritebackRequest` for traceability.

## Auditability and access boundaries
- Manual assignment and reset actions emit immutable audit events.
- View/edit/apply actions are role-gated.
- Cost approval flags are visible in mirror table and stored with each mirrored story.
