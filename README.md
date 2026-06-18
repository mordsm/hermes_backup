# hermes_backup

Backup repository for Hermes-generated artifacts, session snapshots, and curated source exports.

## What goes here
- Report outputs generated during Hermes sessions
- Curated activity summaries
- PDF deliverables and reusable templates
- Source snapshots of key projects/agents

## Latest snapshot
- Date: 2026-06-18
- GitHub branch: `master`
- Latest backup commit: `da60d22`

## Life agent / kanban manager
The life-management agent lives in the backed-up source tree here:

- `task_reminder/app/life_agent/cli.py`
- `task_reminder/app/life_agent/orchestrator.py`
- `task_reminder/app/life_agent/planning.py`
- `task_reminder/app/life_agent/reporting.py`
- `task_reminder/app/life_agent/models.py`

Related wiring:
- `task_reminder/app/cli.py` → `life ...`
- `task_reminder/app/financial_agent/cli.py` → routes follow-ups into `life_agent`

## Backup structure
- `docs/` → human-readable specs and references
- `activity/` → dated session summaries
- `source_snapshots/` → preserved source exports and manifests
- `task_reminder/` → the backed-up application source tree

## Notes
- Sensitive data should be redacted before commit.
- This repo is meant to hold selected artifacts, not raw secrets.
