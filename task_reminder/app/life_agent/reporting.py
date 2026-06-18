from __future__ import annotations

from .models import CalendarBlock, LifeReport, LifeTaskSummary, to_plain


__all__ = ["CalendarBlock", "LifeReport", "LifeTaskSummary", "render_life_report", "to_plain"]


def _task_lines(tasks: list[LifeTaskSummary]) -> list[str]:
    lines: list[str] = []
    for task in tasks:
        if task.due_at:
            lines.append(f"- {task.title} (`{task.status}`, due {task.due_at:%Y-%m-%d %H:%M})")
        else:
            lines.append(f"- {task.title} (`{task.status}`)")
    return lines


def _block_lines(blocks: list[CalendarBlock]) -> list[str]:
    lines: list[str] = []
    for block in blocks:
        lines.append(f"- {block.title} ({block.start:%Y-%m-%d %H:%M})")
    return lines


def render_life_report(report: LifeReport) -> str:
    lines: list[str] = [f"# {report.headline}", ""]
    lines.append(f"- **Period:** {report.period_label}")
    lines.append(f"- **Generated:** {report.generated_at:%Y-%m-%d %H:%M}")
    lines.append("")

    if report.metrics:
        lines.append("## Metrics")
        for key, value in report.metrics.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    if report.completed:
        lines.append("## Completed")
        lines.extend(_task_lines(report.completed))
        lines.append("")

    if report.due_now:
        lines.append("## Due now")
        lines.extend(_task_lines(report.due_now))
        lines.append("")

    if report.blocked:
        lines.append("## Blocked")
        lines.extend(_task_lines(report.blocked))
        lines.append("")

    if report.scheduled:
        lines.append("## Scheduled")
        lines.extend(_task_lines(report.scheduled))
        lines.append("")

    if report.calendar_blocks:
        lines.append("## Calendar blocks")
        lines.extend(_block_lines(report.calendar_blocks))
        lines.append("")

    if report.next_actions:
        lines.append("## Next actions")
        for item in report.next_actions:
            lines.append(f"- {item}")
        lines.append("")

    if report.notes:
        lines.append("## Notes")
        for item in report.notes:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
