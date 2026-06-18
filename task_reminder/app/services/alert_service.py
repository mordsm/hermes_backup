from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from ..config import settings
from ..models import TaskInstance
from ..notifications.console import ConsoleNotifier


class AlertService:
    def __init__(self, session):
        self.session = session
        self.notifier = ConsoleNotifier()

    def _now(self) -> datetime:
        return datetime.now(tz=ZoneInfo(settings.app_timezone))

    def send_due_alerts(self) -> None:
        now = self._now()
        due_instances = self.session.execute(
            select(TaskInstance)
            .where(TaskInstance.status == "pending")
            .where((TaskInstance.snoozed_until.is_(None)) | (TaskInstance.snoozed_until <= now))
            .where((TaskInstance.scheduled_at.is_not(None)) & (TaskInstance.scheduled_at <= now))
        ).scalars().all()

        for instance in due_instances:
            task = instance.task
            title = f"Due: {task.title}"
            message = task.description or "Task is due now."
            self.notifier.send(title, message)
            instance.alert_count += 1
            instance.last_alerted_at = now
