from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .models import AnchorDefinition, AnchorKind


DEFAULT_TIMEZONE = "Asia/Jerusalem"
DEFAULT_ANCHORS = (
    AnchorDefinition(
        key="morning",
        kind=AnchorKind.MORNING,
        title="Morning anchor",
        recurrence_rule="DAILY@07:00",
        start_time="07:00",
        description="Morning review, quick planning, and prioritization.",
    ),
    AnchorDefinition(
        key="evening",
        kind=AnchorKind.EVENING,
        title="Evening anchor",
        recurrence_rule="DAILY@20:00",
        start_time="20:00",
        description="End-of-day review and rollover of unfinished items.",
    ),
    AnchorDefinition(
        key="weekly",
        kind=AnchorKind.WEEKLY,
        title="Weekly review",
        recurrence_rule="WEEKLY@SAT@20:30",
        start_time="20:30",
        description="Motzaei Shabbat review: summarize the past week and plan the next one.",
    ),
    AnchorDefinition(
        key="monthly",
        kind=AnchorKind.MONTHLY,
        title="Monthly review",
        recurrence_rule="MONTHLY_LAST_BUSINESS_DAY@09:00",
        start_time="09:00",
        description="Monthly checkpoint aligned to month-end and external reports.",
    ),
)

WEEKDAY_LOOKUP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


@dataclass(slots=True)
class SchedulePoint:
    label: str
    scheduled_at: datetime


def parse_hhmm(value: str) -> time:
    hour_s, minute_s = value.split(":", 1)
    return time(hour=int(hour_s), minute=int(minute_s))


def localize(day: date, hhmm: str, timezone_name: str = DEFAULT_TIMEZONE) -> datetime:
    tz = ZoneInfo(timezone_name)
    return datetime.combine(day, parse_hhmm(hhmm), tzinfo=tz)


def is_shabbat_like(day: date, holiday_dates: set[date] | None = None) -> bool:
    holiday_dates = holiday_dates or set()
    return day.weekday() == 5 or day in holiday_dates


def previous_business_day(day: date, holiday_dates: set[date] | None = None) -> date:
    holiday_dates = holiday_dates or set()
    candidate = day
    while is_shabbat_like(candidate, holiday_dates):
        candidate -= timedelta(days=1)
    return candidate


def last_business_day_of_month(year: int, month: int, holiday_dates: set[date] | None = None) -> date:
    holiday_dates = holiday_dates or set()
    last_day = date(year, month, monthrange(year, month)[1])
    return previous_business_day(last_day, holiday_dates)


def monthly_review_datetime(
    reference: date | None = None,
    *,
    timezone_name: str = DEFAULT_TIMEZONE,
    holiday_dates: set[date] | None = None,
) -> datetime:
    reference = reference or date.today()
    target_day = last_business_day_of_month(reference.year, reference.month, holiday_dates)
    return localize(target_day, "09:00", timezone_name)


def anchor_schedule_for_period(
    start: date,
    end: date,
    *,
    timezone_name: str = DEFAULT_TIMEZONE,
    holiday_dates: set[date] | None = None,
) -> list[SchedulePoint]:
    holiday_dates = holiday_dates or set()
    points: list[SchedulePoint] = []
    current = start
    while current <= end:
        points.append(SchedulePoint("morning", localize(current, "07:00", timezone_name)))
        points.append(SchedulePoint("evening", localize(current, "20:00", timezone_name)))
        current += timedelta(days=1)

    # weekly on Motzaei Shabbat
    current = start
    while current <= end:
        if current.weekday() == 5:
            points.append(SchedulePoint("weekly", localize(current, "20:30", timezone_name)))
        current += timedelta(days=1)

    monthly_point = monthly_review_datetime(start, timezone_name=timezone_name, holiday_dates=holiday_dates)
    if start <= monthly_point.date() <= end:
        points.append(SchedulePoint("monthly", monthly_point))

    return sorted(points, key=lambda point: point.scheduled_at)


def parse_recurrence_rule(rule: str) -> tuple[str, list[str]]:
    parts = rule.split("@")
    return parts[0], parts[1:]


def recurrence_dates(
    rule: str,
    start: date,
    end: date,
    *,
    holiday_dates: set[date] | None = None,
) -> list[date]:
    holiday_dates = holiday_dates or set()
    kind, parts = parse_recurrence_rule(rule)
    dates: list[date] = []

    if kind == "DAILY" and parts:
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    if kind == "WEEKLY" and len(parts) >= 2:
        weekday_name = parts[0].lower()
        weekday = WEEKDAY_LOOKUP[weekday_name]
        current = start
        while current <= end:
            if current.weekday() == weekday:
                dates.append(current)
            current += timedelta(days=1)
        return dates

    if kind == "MONTHLY_LAST_BUSINESS_DAY" and parts:
        months = {(start.year, start.month), (end.year, end.month)}
        for year, month in sorted(months):
            due = last_business_day_of_month(year, month, holiday_dates)
            if start <= due <= end:
                dates.append(due)
        return dates

    return dates
