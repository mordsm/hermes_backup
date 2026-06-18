# Implementation Plan

## Phase 0: Repo setup

- Create Python package
- Add pyproject.toml
- Add env config
- Add PostgreSQL docker-compose
- Add DB init script
- Add CLI using Typer

## Phase 1: Local core

Implement:

- `tasks`
- `task_instances`
- manual task creation
- daily recurring instance generation
- mark done
- snooze
- skip
- console alerts

Tests:

- completed instance does not reappear
- recurring task generates next instance
- duplicate instance generation is idempotent

## Phase 2: Alert engine

Implement alert query:

- due now
- overdue
- snoozed until now
- stale backlog
- daily digest

Implement alert suppression:

- urgent: repeat after 30 minutes
- high: repeat after 1 hour
- normal: repeat after 4 hours
- backlog: daily/weekly only

## Phase 3: Telegram

Implement Telegram adapter.

Required actions:

- Done
- Snooze 1 hour
- Skip today
- Open source URL

For the MVP, callback handling can be a separate command or FastAPI webhook.

## Phase 4: Google Calendar

Read-only first.

Sync:

- future 30 days
- past 1 day
- incremental sync token if available
- cancelled events become cancelled instances/tasks

Map:

- event.id -> source_object_id
- event.summary -> title
- event.start -> scheduled_at
- event.end -> deadline_at
- event.htmlLink -> source_url
- recurring event -> metadata initially; recurrence expansion can be deferred

Do not mark calendar events done in MVP.

## Phase 5: Google Tasks

Read/write.

Map:

- task.id -> source_object_id
- title -> title
- notes -> description
- due -> due_at/deadline_at
- status completed -> done
- webViewLink/source link if available

Write-back:

- mark completed when local instance is done

## Phase 6: Trello

Read/write.

Map:

- card.id -> source_object_id
- card.name -> title
- card.desc -> description
- card.due -> deadline_at
- card.dueComplete -> done
- card.labels -> category/priority
- card.url -> source_url

Write-back:

- set dueComplete = true
- optional move card to configured Done list

## Phase 7: Dashboard API

Endpoints:

- GET /today
- GET /overdue
- GET /backlog
- GET /upcoming
- POST /instances/{id}/done
- POST /instances/{id}/snooze
- POST /instances/{id}/skip
- GET /sync/status
