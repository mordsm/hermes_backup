from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from ..config import settings
from ..models import TaskInstance
from ..notifications.console import ConsoleNotifier


class CompletionService:
    def __init__(self, session):
        self.session = session

    def _now(self) -> datetime:
        return datetime.now(tz=ZoneInfo(settings.app_timezone))

    def _get_instance(self, instance_id: str) -> TaskInstance:
        instance = self.session.execute(select(TaskInstance).where(TaskInstance.id == instance_id)).scalar_one_or_none()
        if instance is None:
            raise ValueError(f"Task instance not found: {instance_id}")
        return instance

    def mark_done(self, instance_id: str) -> None:
        instance = self._get_instance(instance_id)
        instance.status = "done"
        instance.completed_at = self._now()
        instance.snoozed_until = None

    def snooze(self, instance_id: str, minutes: int) -> None:
        instance = self._get_instance(instance_id)
        instance.status = "pending"
        instance.snoozed_until = self._now() + timedelta(minutes=minutes)

    def skip(self, instance_id: str) -> None:
        instance = self._get_instance(instance_id)
        instance.status = "skipped"
        instance.skipped_at = self._now()
