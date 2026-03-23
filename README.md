# Release Synchronizer

Production-style internal coordination prototype for release planning on top of Azure DevOps.

## Core Workflow (Current)
The app now centers on three views:
1. **Azure Mirror** (`/`): strict source-aligned view grouped by Azure sprint.
2. **Manual Plan** (`/manual/`): release-based planning board with drag-and-drop reassignment.
3. **Diff & Apply** (`/diff/`): compare Azure vs manual placement and choose reset/apply actions.

## What Sync Does
- Pulls **Azure iterations (sprints)**.
- Pulls **Azure User Story work items**.
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

## Azure Env Vars
Set these in `.env`:
- `ADO_ORGANIZATION`
- `ADO_PROJECT`
- `ADO_PAT`
- `ADO_SYNC_INTERVAL_SECONDS` (default `300`)

## Demo Users (seeded)
- `rm_demo` (release manager)
- `eng_demo` (engineering lead)
- `fin_demo` (finance approver)
- `vc_demo` (vendor coordinator)
- `vendor_demo` (vendor user)
- `exec_demo` (executive viewer)

Default password: `ChangeMe123!` (override with `--password`).

