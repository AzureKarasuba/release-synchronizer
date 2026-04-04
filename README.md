# Release Synchronizer

Production-style internal coordination prototype for release planning on top of Azure DevOps.

## Core Workflow (Current)
The app now centers on four views:
1. **Azure Mirror** (`/`): strict source-aligned view grouped by Azure sprint.
2. **Manual Plan** (`/manual/`): release-based planning board with drag-and-drop reassignment.
3. **Diff View** (`/diff/`): compare Azure vs manual placement and optionally reset local assignment to Azure default.
4. **Status Report** (`/status-report/`): shared editable status list + verified email subscription for daily digest.

## Demo Access Mode
- Public demo mode is enabled by default (`DEMO_PUBLIC_MODE=True`).
- Login button is intentionally a placeholder for the demo UX.
- In production, restore authentication/authorization before external use.

## What Sync Does
- Pulls **Azure iterations (sprints)**.
- Pulls **Azure User Story work items** (including parent feature metadata when available).
- Upserts ticket fields: ID, title, assignee, state, sprint, target date.
- Auto-creates release buckets from sprint structure (default behavior).

## Setup
1. Create and activate virtual environment.
2. Install dependencies.
3. Configure `.env` from `.env.example`.
4. Run migrations.
5. Seed demo data (optional).

```bash
python manage.py migrate
python manage.py seed_demo_data
```

## Run
```bash
python manage.py runserver
```

## Azure Sync Commands
- One-shot sync:
```bash
python manage.py sync_ado --force
```

- Continuous sync worker (every 5 minutes by default):
```bash
python manage.py run_ado_sync_worker --interval 300
```

## Status Report Email Commands
- Send daily digest to verified subscribers:
```bash
python manage.py send_status_report_digest
```

## Azure Env Vars
Set these in `.env`:
- `ADO_ORGANIZATION`
- `ADO_PROJECT`
- `ADO_PAT`
- `ADO_SYNC_INTERVAL_SECONDS` (default `300`)
- `ADO_WORK_ITEM_TYPES` (default `User Story,Product Backlog Item`)

## Demo + Email Env Vars
- `DEMO_PUBLIC_MODE=True`
- `SITE_BASE_URL=http://127.0.0.1:8000`
- `DEFAULT_FROM_EMAIL=noreply@release-synchronizer.local`
- `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` (local default)
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` for real SMTP

## Replace Demo Tickets With Your Azure Data
If you ran `seed_demo_data`, two sample rows are inserted (`#10101`, `#10102`).
To switch to your real Azure data:

```bash
python manage.py sync_ado --force
```

If sample rows still appear, clear local ticket cache once and re-sync:

```bash
python manage.py shell -c "from apps.integrations.models import ADOUserStory; ADOUserStory.objects.all().delete()"
python manage.py sync_ado --force
```

## Demo Users (seeded)
- `rm_demo` (release manager)
- `eng_demo` (engineering lead)
- `fin_demo` (finance approver)
- `vc_demo` (vendor coordinator)
- `vendor_demo` (vendor user)
- `exec_demo` (executive viewer)

Default password: `ChangeMe123!` (override with `--password`).
