# Release Synchronizer

Production-style internal coordination tool prototype built with Django.

## Purpose
Release Synchronizer adds a business-controlled coordination layer on top of Azure DevOps execution tracking:
- Manual release plan management with change reasons
- Cost approval lifecycle tracking
- Release-to-sprint mapping
- Vendor action queue and follow-up
- Mismatch detection and triage
- Auditability with role-aware visibility

## Quick Start
1. Create virtual environment and install dependencies.
2. Set env vars from `.env.example`.
3. Run migrations:
   - `python manage.py migrate`
4. Create admin user:
   - `python manage.py createsuperuser`
5. Seed demo data (optional but recommended):
   - `python manage.py seed_demo_data`
6. Start server:
   - `python manage.py runserver`

## Demo Users (from seed command)
- `rm_demo` (release manager)
- `eng_demo` (engineering lead)
- `fin_demo` (finance approver)
- `vc_demo` (vendor coordinator)
- `vendor_demo` (vendor user)
- `exec_demo` (executive viewer)

Default password: `ChangeMe123!` (override via `--password` when seeding).

## Role-Based Visibility Rules (MVP)
- Cost fields are visible only to release manager, finance approver, and system admin.
- Vendor users only see vendor actions assigned to themselves.
- Audit and mismatch APIs are restricted to internal staff roles.
- Vendor users can update only vendor action status through dedicated workflow.

## Management Commands
- `python manage.py assign_role <username> <role>`
- `python manage.py import_ado_snapshot <csv_path> --project <project_name>`
- `python manage.py run_mismatch_scan`
- `python manage.py seed_demo_data [--password <value>]`

## Key API Endpoints
- `POST /api/mismatch-scan/run`
- `GET /api/releases/<release_item_id>/mismatches`
- `POST /api/vendor-actions/<action_id>/status`
- `GET /api/audit-events`
- `POST /api/ado/sprint-snapshots/import`

## Apps
- `apps/releases`: release plans and release items
- `apps/approvals`: cost approval workflow
- `apps/integrations`: Azure DevOps sprint snapshots
- `apps/mappings`: release-to-sprint mapping
- `apps/vendor_queue`: vendor follow-up queue
- `apps/mismatch`: mismatch detection findings
- `apps/audit`: append-only audit events
- `apps/accounts`: role bootstrap and user account helpers
- `apps/api`: integration and operational endpoints
- `apps/common`: shared base classes and utilities
