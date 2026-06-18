# Personal Task Reminder System

A personal task orchestration system using:

- PostgreSQL as the operational source of truth
- Google Calendar for fixed-time events
- Google Tasks for personal tasks
- Trello for backlog/projects/kanban
- Telegram Bot for actionable alerts
- Windows Task Scheduler as the periodic trigger

The first MVP is intentionally conservative:
- Read from Google Calendar, Google Tasks, Trello
- Normalize into PostgreSQL
- Generate task instances
- Detect due/overdue/stale backlog items
- Send Telegram alerts
- Allow local completion/snooze/skip
- Write completion back only to the original source where safe

## Recommended stack

- Python 3.12+
- PostgreSQL 16+
- SQLAlchemy 2.x
- Alembic
- FastAPI
- Typer CLI
- python-dateutil
- google-api-python-client
- py-trello or direct Trello REST
- python-telegram-bot

## Main commands to implement

```bash
taskreminder sync
taskreminder generate-instances
taskreminder alert
taskreminder run-once
taskreminder mark-done <instance-id>
taskreminder snooze <instance-id> --minutes 60
taskreminder skip <instance-id>
taskreminder serve
```

`run-once` is the command Windows Task Scheduler should invoke hourly.

## MVP boundary

Do not implement every integration perfectly in the first iteration.

Priority order:

1. PostgreSQL schema + domain model
2. Manual/local tasks
3. Recurring daily tasks
4. Telegram alerts
5. Google Calendar read-only sync
6. Google Tasks read/write
7. Trello read/write
8. Dashboard API
9. Google Keep inbox only, optional and later
