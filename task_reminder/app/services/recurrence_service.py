from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from ..config import settings
from ..models import Task, TaskInstance
from ..life_agent.planning import localize, parse_recurrence_rule, recurrence_dates


class RecurrenceService:
    def __init__(self, session):
        self.session = session

    def _now(self) -> datetime:
        return datetime.now(tz=ZoneInfo(settings.app_timezone))

    def generate_instances(self) -> None:
        today = self._now().date()
        horizon = today + timedelta(days=7)
        recurring_tasks = self.session.execute(
            select(Task).where(Task.task_type == "recurring", Task.archived_at.is_(None))
        ).scalars().all()

        for task in recurring_tasks:
            rule_kind, rule_parts = parse_recurrence_rule(task.recurrence_rule or "")
            hhmm = "09:00"
            if rule_kind == "DAILY" and rule_parts:
                hhmm = rule_parts[0]
            elif rule_kind == "WEEKLY" and len(rule_parts) >= 2:
                hhmm = rule_parts[1]
            elif rule_kind == "MONTHLY_LAST_BUSINESS_DAY" and rule_parts:
                hhmm = rule_parts[0]

            for occ in recurrence_dates(task.recurrence_rule or "", today, horizon):
                exists = self.session.execute(
                    select(TaskInstance).where(TaskInstance.task_id == task.id, TaskInstance.occurrence_date == occ)
                ).scalar_one_or_none()
                if exists is not None:
                    continue
                scheduled_at = localize(occ, hhmm, settings.app_timezone)
                self.session.add(
                    TaskInstance(
                        task_id=task.id,
                        occurrence_date=occ,
                        scheduled_at=scheduled_at,
                        deadline_at=scheduled_at,
                        status="pending",
                        completed_at=None,
                        skipped_at=None,
                        snoozed_until=None,
                        alert_count=0,
                        last_alerted_at=None,
                        created_at=self._now(),
                    )
                )
