from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class AnchorKind(str, Enum):
    MORNING = "morning"
    EVENING = "evening"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass(slots=True)
class AnchorDefinition:
    key: str
    kind: AnchorKind
    title: str
    recurrence_rule: str
    start_time: str
    description: str


@dataclass(slots=True)
class LifeTaskSummary:
    id: str
    title: str
    status: str
    source: str = "local"
    category: str | None = None
    task_type: str = "single"
    due_at: datetime | None = None
    deadline_at: datetime | None = None
    source_url: str | None = None


@dataclass(slots=True)
class CalendarBlock:
    title: str
    start: datetime
    end: datetime | None = None
    location: str | None = None
    status: str = "scheduled"
    source: str = "google_calendar"
    source_object_id: str | None = None
    source_url: str | None = None


@dataclass(slots=True)
class LifeReport:
    report_type: str
    headline: str
    period_label: str
    generated_at: datetime
    completed: list[LifeTaskSummary] = field(default_factory=list)
    due_now: list[LifeTaskSummary] = field(default_factory=list)
    blocked: list[LifeTaskSummary] = field(default_factory=list)
    scheduled: list[LifeTaskSummary] = field(default_factory=list)
    calendar_blocks: list[CalendarBlock] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CalendarSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    blocks: list[CalendarBlock] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IntakeResult:
    task: LifeTaskSummary
    created: bool = True
    note: str | None = None


def to_plain(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dataclass_fields__") and not isinstance(obj, type):
        return {key: to_plain(value) for key, value in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_plain(item) for item in obj]
    if isinstance(obj, dict):
        return {key: to_plain(value) for key, value in obj.items()}
    if isinstance(obj, Enum):
        return obj.value
    return obj
