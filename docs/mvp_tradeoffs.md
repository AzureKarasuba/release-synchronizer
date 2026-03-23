# MVP Tradeoffs

## Included now
- Strong data model for releases, approvals, mappings, vendor actions, mismatch findings, and audit events.
- Role-based visibility and basic object-level constraints for vendor users.
- Management commands for import, mismatch scan, role assignment, and demo seeding.

## Deferred to next iteration
- Bi-directional Azure DevOps sync.
- Notification and escalation channels (Slack/Teams/email).
- Field-level encryption and advanced masking policy engine.
- Async workers (Celery/Redis) and retry orchestration for long-running jobs.

## Why this split
This keeps the prototype realistic and interview-credible while remaining implementable by one engineer in a short timeline.
