from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from ..connectors.google_calendar import GoogleCalendarConnector
from ..connectors.google_tasks import GoogleTasksConnector
from ..connectors.trello import TrelloConnector
from ..models import Task
from ..config import settings


class SyncService:
    def __init__(self, session):
        self.session = session

    def _now(self) -> datetime:
        return datetime.now(tz=ZoneInfo(settings.app_timezone))

    def _upsert_task(self, *, source: str, source_object_id: str, title: str, description: str | None, due_at: datetime | None, deadline_at: datetime | None, source_url: str | None, task_type: str, status: str, category: str, metadata: dict | None = None) -> None:
        stmt = select(Task).where(Task.source == source, Task.source_object_id == source_object_id)
        task = self.session.execute(stmt).scalar_one_or_none()
        now = self._now()
        if task is None:
            task = Task(
                title=title,
                description=description,
                status=status,
                priority="normal",
                category=category,
                task_type=task_type,
                due_at=due_at,
                deadline_at=deadline_at,
                recurrence_rule=None,
                timezone=settings.app_timezone,
                source=source,
                source_object_id=source_object_id,
                source_url=source_url,
                metadata_=metadata or {},
                created_at=now,
                updated_at=now,
                archived_at=None,
            )
            self.session.add(task)
            return

        task.title = title
        task.description = description
        task.due_at = due_at
        task.deadline_at = deadline_at
        task.source_url = source_url
        task.task_type = task_type
        task.status = status
        task.category = category
        task.updated_at = now
        task.metadata_ = metadata or task.metadata_ or {}

    def sync_all(self) -> None:
        calendar_items = GoogleCalendarConnector().sync()
        for item in calendar_items:
            self._upsert_task(
                source=item.source,
                source_object_id=item.source_object_id,
                title=item.title,
                description=item.description,
                due_at=item.due_at,
                deadline_at=item.deadline_at,
                source_url=item.source_url,
                task_type="calendar_event",
                status="scheduled",
                category="calendar_block",
                metadata=item.raw,
            )

        # Google Tasks and Trello remain optional connectors; keep the hooks live.
        _ = GoogleTasksConnector().sync()
        _ = TrelloConnector().sync()
