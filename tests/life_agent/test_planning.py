from datetime import date

from task_reminder.app.life_agent.planning import last_business_day_of_month, monthly_review_datetime, recurrence_dates


def test_last_business_day_skips_shabbat():
    assert last_business_day_of_month(2026, 1) == date(2026, 1, 30)


def test_last_business_day_skips_holiday_like_day():
    assert last_business_day_of_month(2026, 1, {date(2026, 1, 30)}) == date(2026, 1, 29)


def test_monthly_review_datetime_uses_9am():
    dt = monthly_review_datetime(date(2026, 8, 10))
    assert dt.hour == 9 and dt.minute == 0


def test_daily_recurrence_spans_range():
    dates = recurrence_dates("DAILY@07:00", date(2026, 8, 1), date(2026, 8, 3))
    assert dates == [date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3)]
