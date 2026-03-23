# Architecture Notes

## Source of truth boundaries
- Azure DevOps remains source of truth for sprint execution artifacts.
- Release Synchronizer is source of truth for business release coordination metadata.
- Integration is one-way in MVP: ADO snapshot ingestion into internal planning context.

## Key consistency model
- Eventual consistency is expected between release plans and ADO snapshots.
- Mismatch findings make inconsistencies explicit and actionable instead of hiding them.

## Auditability
- All material workflow changes emit immutable audit events with actor, reason, and before/after payload.
- Request correlation is captured with request ID propagation middleware.

## Permissions
- Role checks are enforced both at view/API layer and in list/queryset filtering for vendor users.
- Sensitive cost fields are conditionally disclosed by role.
