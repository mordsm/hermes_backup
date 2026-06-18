# Architecture

## Core principle

The system is a local operational task engine with external connectors.

```text
Windows Task Scheduler
        |
        v
CLI: taskreminder run-once
        |
        +--> acquire PostgreSQL advisory lock
        +--> sync external sources
        +--> normalize/update tasks
        +--> generate recurring task instances
        +--> find due/overdue/stale items
        +--> send alerts
        +--> persist alert history
        +--> release lock
```

## Components

### PostgreSQL

Stores:

- tasks
- task_instances
- external_links
- sync_state
- alerts
- audit_log
- settings

### Connectors

Each connector implements:

```python
class Connector:
    source_name: str

    def sync(self) -> list[ExternalItem]:
        ...

    def mark_done(self, source_object_id: str) -> None:
        ...

    def get_source_url(self, source_object_id: str) -> str | None:
        ...
```

### Recurrence service

Responsible for creating future `task_instances` from recurring `tasks`.

Rules:

- Generate at least today and tomorrow for daily tasks
- Never duplicate instances
- Use unique constraint `(task_id, occurrence_date)`
- Do not generate for archived/cancelled tasks

### Alert service

Responsible for:

- finding due and overdue task instances
- suppressing duplicate alerts
- building alert text
- dispatching via configured channels

### Completion service

Responsible for:

- marking an instance done
- writing back to original source if enabled and safe
- preventing completed instances from reappearing

## Recommended first data flow

1. Create local recurring tasks manually
2. Generate today's instances
3. Alert via console
4. Add Telegram
5. Add Google Calendar read-only
6. Add Google Tasks
7. Add Trello
