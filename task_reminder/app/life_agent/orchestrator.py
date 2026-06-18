from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from ..connectors.google_calendar import GoogleCalendarConnector
from ..models import Task, TaskInstance
from .models import CalendarBlock, CalendarSyncResult, IntakeResult, LifeReport, LifeTaskSummary, AnchorKind
from .planning import DEFAULT_ANCHORS, last_business_day_of_month, localize, monthly_review_datetime, parse_recurrence_rule, recurrence_dates


class LifeAgent:
    def __init__(self, session, timezone_name: str = "Asia/Jerusalem"):
        self.session = session
        self.timezone_name = timezone_name

    def _now(self) -> datetime:
        return datetime.now(tz=ZoneInfo(self.timezone_name))

    def _next_business_morning(self) -> datetime:
        now = self._now()
        candidate = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate = candidate + timedelta(days=1)
        return candidate

    def _task_summary(self, task: Task) -> LifeTaskSummary:
        return LifeTaskSummary(
            id=str(task.id),
            title=task.title,
            status=task.status,
            source=task.source,
            category=task.category,
            task_type=task.task_type,
            due_at=task.due_at,
            deadline_at=task.deadline_at,
            source_url=task.source_url,
        )

    def _instance_summary(self, instance: TaskInstance, task: Task) -> LifeTaskSummary:
        return LifeTaskSummary(
            id=str(instance.id),
            title=task.title,
            status=instance.status,
            source=task.source,
            category=task.category,
            task_type=task.task_type,
            due_at=instance.scheduled_at or instance.deadline_at or task.due_at,
            deadline_at=instance.deadline_at or task.deadline_at,
            source_url=task.source_url,
        )

    def _calendar_block(self, task: Task) -> CalendarBlock:
        start = task.due_at or task.deadline_at or self._now()
        end = task.deadline_at or (start + timedelta(minutes=30))
        return CalendarBlock(
            title=task.title,
            start=start,
            end=end,
            source=task.source,
            source_object_id=task.source_object_id,
            source_url=task.source_url,
        )

    def _query_tasks(self, *conditions) -> list[Task]:
        stmt = select(Task).where(*conditions).order_by(Task.due_at.nullslast(), Task.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def _query_instances(self, *conditions) -> list[TaskInstance]:
        stmt = select(TaskInstance).join(Task).where(*conditions).order_by(TaskInstance.scheduled_at.nullslast())
        return list(self.session.execute(stmt).scalars().all())

    def seed_default_anchors(self) -> list[Task]:
        created: list[Task] = []
        now = self._now()
        for anchor in DEFAULT_ANCHORS:
            stmt = select(Task).where(Task.source == "life_agent", Task.source_object_id == f"anchor:{anchor.key}")
            existing = self.session.execute(stmt).scalar_one_or_none()
            if existing is not None:
                continue
            task = Task(
                title=anchor.title,
                description=anchor.description,
                status="active",
                priority="high" if anchor.kind in {AnchorKind.MORNING, AnchorKind.EVENING} else "normal",
                category="life_anchor",
                task_type="recurring",
                due_at=monthly_review_datetime(date.today(), timezone_name=self.timezone_name) if anchor.kind is AnchorKind.MONTHLY else None,
                deadline_at=None,
                recurrence_rule=anchor.recurrence_rule,
                timezone=self.timezone_name,
                source="life_agent",
                source_object_id=f"anchor:{anchor.key}",
                source_url=None,
                metadata_={"anchor_kind": anchor.kind.value, "start_time": anchor.start_time},
                created_at=now,
                updated_at=now,
                archived_at=None,
            )
            self.session.add(task)
            created.append(task)
        return created

    def ingest_task(
        self,
        title: str,
        description: str | None = None,
        *,
        category: str | None = None,
        source: str = "manual",
        source_object_id: str | None = None,
        source_url: str | None = None,
        due_at: datetime | None = None,
        deadline_at: datetime | None = None,
        task_type: str = "single",
        priority: str = "normal",
        recurrence_rule: str | None = None,
        metadata: dict | None = None,
        status: str = "active",
    ) -> IntakeResult:
        now = self._now()
        if source_object_id is not None:
            stmt = select(Task).where(Task.source == source, Task.source_object_id == source_object_id)
            existing = self.session.execute(stmt).scalar_one_or_none()
            if existing is not None:
                existing.title = title
                existing.description = description
                existing.category = category
                existing.task_type = task_type
                existing.due_at = due_at
                existing.deadline_at = deadline_at
                existing.recurrence_rule = recurrence_rule
                existing.priority = priority
                existing.source_url = source_url
                existing.metadata_ = metadata or existing.metadata_ or {}
                existing.status = status
                existing.updated_at = now
                return IntakeResult(task=self._task_summary(existing), created=False)

        task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            category=category,
            task_type=task_type,
            due_at=due_at,
            deadline_at=deadline_at,
            recurrence_rule=recurrence_rule,
            timezone=self.timezone_name,
            source=source,
            source_object_id=source_object_id,
            source_url=source_url,
            metadata_=metadata or {},
            created_at=now,
            updated_at=now,
            archived_at=None,
        )
        self.session.add(task)
        self.session.flush()
        return IntakeResult(task=self._task_summary(task), created=True)

    def ingest_financial_followup(
        self,
        title: str,
        description: str | None = None,
        *,
        source_object_id: str | None = None,
        source_url: str | None = None,
        due_at: datetime | None = None,
        metadata: dict | None = None,
    ) -> IntakeResult:
        payload = {"routing": "financial_followup", **(metadata or {})}
        due_at = due_at or self._next_business_morning()
        return self.ingest_task(
            title,
            description,
            category="financial_followup",
            source="financial_agent",
            source_object_id=source_object_id,
            source_url=source_url,
            due_at=due_at,
            task_type="single",
            priority="high",
            metadata=payload,
            status="scheduled",
        )

    def sync_calendar(self) -> CalendarSyncResult:
        connector = GoogleCalendarConnector()
        result = CalendarSyncResult()
        for item in connector.sync():
            start = item.due_at or self._now()
            end = item.deadline_at or (start + timedelta(minutes=30))
            stmt = select(Task).where(Task.source == item.source, Task.source_object_id == item.source_object_id)
            task = self.session.execute(stmt).scalar_one_or_none()
            if task is None:
                task = Task(
                    title=item.title,
                    description=item.description,
                    status="scheduled",
                    priority="normal",
                    category="calendar_block",
                    task_type="calendar_event",
                    due_at=start,
                    deadline_at=end,
                    recurrence_rule=None,
                    timezone=self.timezone_name,
                    source=item.source,
                    source_object_id=item.source_object_id,
                    source_url=item.source_url,
                    metadata_=item.raw or {},
                    created_at=self._now(),
                    updated_at=self._now(),
                    archived_at=None,
                )
                self.session.add(task)
                result.created += 1
            else:
                task.title = item.title
                task.description = item.description
                task.due_at = start
                task.deadline_at = end
                task.status = "scheduled"
                task.updated_at = self._now()
                task.metadata_ = item.raw or task.metadata_ or {}
                result.updated += 1
            result.blocks.append(CalendarBlock(title=item.title, start=start, end=end, location=None, source=item.source, source_object_id=item.source_object_id, source_url=item.source_url))
        return result

    def generate_anchor_instances(self, horizon_days: int = 7, holiday_dates: set[date] | None = None) -> int:
        today = datetime.now(tz=ZoneInfo(self.timezone_name)).date()
        end = today + timedelta(days=horizon_days)
        created = 0
        recurring_tasks = self._query_tasks(Task.task_type == "recurring", Task.archived_at.is_(None))
        for task in recurring_tasks:
            rule_kind, rule_parts = parse_recurrence_rule(task.recurrence_rule or "")
            hhmm = "09:00"
            if rule_kind == "DAILY" and rule_parts:
                hhmm = rule_parts[0]
            elif rule_kind == "WEEKLY" and len(rule_parts) >= 2:
                hhmm = rule_parts[1]
            elif rule_kind == "MONTHLY_LAST_BUSINESS_DAY" and rule_parts:
                hhmm = rule_parts[0]

            for occ in recurrence_dates(task.recurrence_rule or "", today, end, holiday_dates=holiday_dates):
                scheduled_at = localize(occ, hhmm, self.timezone_name)
                stmt = select(TaskInstance).where(TaskInstance.task_id == task.id, TaskInstance.occurrence_date == occ)
                existing = self.session.execute(stmt).scalar_one_or_none()
                if existing is not None:
                    continue
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
                created += 1
        return created


    def build_daily_report(self, report_date: date | None = None) -> LifeReport:
        report_date = report_date or datetime.now(tz=ZoneInfo(self.timezone_name)).date()
        start = datetime.combine(report_date, datetime.min.time(), tzinfo=ZoneInfo(self.timezone_name))
        end = start + timedelta(days=1)
        completed_instances = self._query_instances(TaskInstance.status == "done", TaskInstance.completed_at >= start, TaskInstance.completed_at < end)
        due_instances = self._query_instances(TaskInstance.status == "pending", TaskInstance.scheduled_at >= start, TaskInstance.scheduled_at < end)
        blocked = self._query_tasks(Task.status == "blocked", Task.archived_at.is_(None))
        scheduled = self._query_tasks(Task.status == "scheduled", Task.archived_at.is_(None))
        calendar_blocks = [self._calendar_block(task) for task in scheduled if task.source == "google_calendar" or task.task_type == "calendar_event"]
        metrics = {
            "completed": len(completed_instances),
            "due_now": len(due_instances),
            "blocked": len(blocked),
            "scheduled": len(scheduled),
        }
        next_actions = [
            "Keep today to the minimum viable plan.",
            "Move blocked items to a concrete next step.",
            "Use the Inbox for any new file uploads or financial follow-ups.",
        ]
        notes = ["Daily report focuses on current-day execution and friction."]
        return LifeReport(
            report_type="daily",
            headline="Daily life-management report",
            period_label=report_date.isoformat(),
            generated_at=self._now(),
            completed=[self._instance_summary(instance, instance.task) for instance in completed_instances],
            due_now=[self._instance_summary(instance, instance.task) for instance in due_instances],
            blocked=[self._task_summary(task) for task in blocked],
            scheduled=[self._task_summary(task) for task in scheduled],
            calendar_blocks=calendar_blocks,
            next_actions=next_actions,
            notes=notes,
            metrics=metrics,
        )

    def build_weekly_report(self, report_date: date | None = None) -> LifeReport:
        report_date = report_date or datetime.now(tz=ZoneInfo(self.timezone_name)).date()
        week_start = report_date - timedelta(days=6)
        start = datetime.combine(week_start, datetime.min.time(), tzinfo=ZoneInfo(self.timezone_name))
        end = datetime.combine(report_date + timedelta(days=1), datetime.min.time(), tzinfo=ZoneInfo(self.timezone_name))
        completed_instances = self._query_instances(TaskInstance.status == "done", TaskInstance.completed_at >= start, TaskInstance.completed_at < end)
        due_instances = self._query_instances(TaskInstance.status == "pending", TaskInstance.scheduled_at >= start, TaskInstance.scheduled_at < end)
        blocked = self._query_tasks(Task.status == "blocked", Task.archived_at.is_(None))
        scheduled = self._query_tasks(Task.status == "scheduled", Task.archived_at.is_(None))
        calendar_blocks = [self._calendar_block(task) for task in scheduled if task.source == "google_calendar" or task.task_type == "calendar_event"]
        metrics = {
            "completed": len(completed_instances),
            "due_in_week": len(due_instances),
            "blocked": len(blocked),
            "calendar_blocks": len(calendar_blocks),
        }
        next_actions = [
            "Review carry-over items and convert them into clear next actions.",
            "Reserve calendar blocks for the highest-value tasks only.",
            "Keep the recurring anchors on the board, but avoid calendar clutter.",
        ]
        notes = ["Weekly report is past + next week planning in one pass."]
        return LifeReport(
            report_type="weekly",
            headline="Weekly life-management report",
            period_label=f"{week_start.isoformat()} → {report_date.isoformat()}",
            generated_at=self._now(),
            completed=[self._instance_summary(instance, instance.task) for instance in completed_instances],
            due_now=[self._instance_summary(instance, instance.task) for instance in due_instances],
            blocked=[self._task_summary(task) for task in blocked],
            scheduled=[self._task_summary(task) for task in scheduled],
            calendar_blocks=calendar_blocks,
            next_actions=next_actions,
            notes=notes,
            metrics=metrics,
        )

    def build_monthly_report(self, report_date: date | None = None, holiday_dates: set[date] | None = None) -> LifeReport:
        report_date = report_date or datetime.now(tz=ZoneInfo(self.timezone_name)).date()
        month_start = date(report_date.year, report_date.month, 1)
        start = datetime.combine(month_start, datetime.min.time(), tzinfo=ZoneInfo(self.timezone_name))
        end = datetime.combine(report_date + timedelta(days=1), datetime.min.time(), tzinfo=ZoneInfo(self.timezone_name))
        completed_instances = self._query_instances(TaskInstance.status == "done", TaskInstance.completed_at >= start, TaskInstance.completed_at < end)
        due_instances = self._query_instances(TaskInstance.status == "pending", TaskInstance.scheduled_at >= start, TaskInstance.scheduled_at < end)
        blocked = self._query_tasks(Task.status == "blocked", Task.archived_at.is_(None))
        scheduled = self._query_tasks(Task.status == "scheduled", Task.archived_at.is_(None))
        calendar_blocks = [self._calendar_block(task) for task in scheduled if task.source == "google_calendar" or task.task_type == "calendar_event"]
        monthly_due = monthly_review_datetime(report_date, timezone_name=self.timezone_name, holiday_dates=holiday_dates)
        metrics = {
            "completed": len(completed_instances),
            "due_in_month": len(due_instances),
            "blocked": len(blocked),
            "calendar_blocks": len(calendar_blocks),
            "monthly_review_due_at": monthly_due.isoformat(),
        }
        next_actions = [
            "Audit the month's carry-over load and remove tasks that no longer matter.",
            "Keep the calendar for time blocks only; leave the task detail in Kanban.",
            "Route any new financial follow-ups into the life-management inbox for now.",
        ]
        notes = [f"Monthly review is aligned to {monthly_due.strftime('%Y-%m-%d %H:%M')}."]
        return LifeReport(
            report_type="monthly",
            headline="Monthly life-management report",
            period_label=f"{month_start.isoformat()} → {report_date.isoformat()}",
            generated_at=self._now(),
            completed=[self._instance_summary(instance, instance.task) for instance in completed_instances],
            due_now=[self._instance_summary(instance, instance.task) for instance in due_instances],
            blocked=[self._task_summary(task) for task in blocked],
            scheduled=[self._task_summary(task) for task in scheduled],
            calendar_blocks=calendar_blocks,
            next_actions=next_actions,
            notes=notes,
            metrics=metrics,
        )

