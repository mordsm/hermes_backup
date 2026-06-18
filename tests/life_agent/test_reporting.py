from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from task_reminder.app.life_agent.models import CalendarBlock, LifeReport, LifeTaskSummary
from task_reminder.app.life_agent.reporting import render_life_report


def test_render_life_report_includes_sections():
    report = LifeReport(
        report_type="daily",
        headline="Daily life-management report",
        period_label="2026-08-01",
        generated_at=datetime(2026, 8, 1, 7, 0, tzinfo=ZoneInfo("Asia/Jerusalem")),
        completed=[LifeTaskSummary(id="1", title="Finish report", status="done")],
        due_now=[LifeTaskSummary(id="2", title="Call bank", status="pending")],
        blocked=[],
        scheduled=[],
        calendar_blocks=[CalendarBlock(title="Family meeting", start=datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc))],
        next_actions=["Protect the morning block."],
        notes=["Test note."],
        metrics={"completed": 1},
    )

    text = render_life_report(report)
    assert "Daily life-management report" in text
    assert "## Completed" in text
    assert "Finish report" in text
    assert "## Calendar blocks" in text
