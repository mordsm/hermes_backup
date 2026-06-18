# Codex Task

Build the MVP of a personal task reminder system.

## Product goal

Create a local-first task orchestration system that reads tasks/events from external tools, normalizes them into PostgreSQL, generates actionable task instances, and alerts the user when an item is due, overdue, stale, or not completed.

The system must support:

1. Backlog tasks with no specific due time
2. Daily recurring tasks with no fixed hour
3. Daily recurring tasks at a fixed hour
4. Tasks with a deadline, such as "do by 16:00"
5. Tasks at a specific date and time
6. Completion behavior:
   - Once a task instance is completed, it must not appear again
   - For recurring tasks, only the current instance is completed; the next occurrence is generated when needed

## Chosen architecture

- PostgreSQL is the operational source of truth
- Google Calendar is used for fixed-time events
- Google Tasks is used for personal actionable tasks
- Trello is used for backlog and project/kanban tasks
- Telegram Bot is used for alerts and quick actions
- Windows Task Scheduler runs the program periodically, initially every hour
- Optional local FastAPI dashboard exposes Today, Overdue, Backlog, and Sync Status

## Implementation instructions

Use Python 3.12.

Use the following structure:

```text
task_reminder/
  app/
    main.py
    config.py
    db.py
    models.py
    schemas.py
    cli.py
    services/
      sync_service.py
      recurrence_service.py
      alert_service.py
      completion_service.py
      dedup_service.py
    connectors/
      base.py
      google_calendar.py
      google_tasks.py
      trello.py
    notifications/
      telegram.py
      console.py
    api/
      routes.py
      server.py
  migrations/
  tests/
  pyproject.toml
  docker-compose.yml
  .env.example
```

## Critical design rules

### 1. PostgreSQL is the operational truth

External tools are not allowed to dictate runtime logic directly.

The system first syncs external objects into PostgreSQL, then all due/overdue/alert decisions are made from PostgreSQL.

### 2. Separate tasks from task instances

A recurring task is not the same as today's required action.

Use:

- `tasks` for task templates/source objects
- `task_instances` for concrete executable occurrences

Example:

- Task: "Take medicine every day at 09:00"
- Instance: "Take medicine on 2026-05-11 at 09:00"

Completing the instance must not archive the recurring task.

### 3. Avoid alert spam

A pending backlog task without due time must not alert every hourly run.

Suggested rules:

- Fixed-time tasks: alert when scheduled_at <= now
- Deadline tasks: alert before and after deadline according to policy
- Daily no-time tasks: include in daily digest
- Backlog tasks: include in daily/weekly planning or stale backlog alert after age threshold
- Do not alert the same task instance repeatedly unless repeat interval has passed

### 4. Conservative write-back

For MVP:

- Google Calendar: read-only
- Google Tasks: can mark completed
- Trello: can set dueComplete or move to Done list
- Local tasks: local only

Do not create cross-tool duplicates automatically.

### 5. Use advisory lock

The hourly runner must use PostgreSQL advisory lock so two runs cannot send duplicate alerts.

Use:

```sql
SELECT pg_try_advisory_lock(987654321);
```

Release at the end:

```sql
SELECT pg_advisory_unlock(987654321);
```

### 6. Audit everything important

Any sync update, alert, completion, snooze, skip, or external write-back should be logged to `audit_log`.

## Deliverables

Implement:

1. Database models
2. Alembic migration or raw SQL init
3. CLI commands
4. Recurrence generation
5. Due/overdue query logic
6. Telegram notification adapter
7. Stub connectors for Google Calendar, Google Tasks, Trello
8. FastAPI read-only dashboard endpoints
9. Unit tests for recurrence, completion, alert suppression, and idempotent sync
10. README with setup instructions

## Acceptance criteria

A user can:

1. Start PostgreSQL with docker compose
2. Run migrations
3. Create local test tasks
4. Generate today's recurring instances
5. Run `taskreminder run-once`
6. Receive or print alerts
7. Mark an instance done
8. Run again and confirm the done instance does not reappear
9. Confirm recurring tasks generate the next occurrence
10. View Today/Overdue/Backlog from API endpoints
