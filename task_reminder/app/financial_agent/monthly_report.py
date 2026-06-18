from __future__ import annotations

from .models import MonthlyReport, to_plain


class MonthlyReportGenerator:
    def render_markdown(self, report: MonthlyReport) -> str:
        lines = [f"# {report.headline}", ""]
        sections = [
            ("Facts", report.facts),
            ("Assumptions", report.assumptions),
            ("Missing information", report.missing_information),
            ("Recommendations", report.recommendations),
            ("Risks", report.risks),
            ("Manual approval actions", report.manual_approval_actions),
            ("Questions for Moshe", report.questions_for_moshe),
            ("Budget summary", report.budget_summary),
            ("Cashflow summary", report.cashflow_summary),
            ("Investment summary", report.investment_summary),
            ("Decision log highlights", report.decision_log_highlights),
        ]
        for title, value in sections:
            lines.append(f"## {title}")
            if isinstance(value, list):
                if not value:
                    lines.append("- None")
                else:
                    for item in value:
                        lines.append(f"- {to_plain(item)}")
            elif isinstance(value, dict):
                if not value:
                    lines.append("- None")
                else:
                    for key, item in value.items():
                        lines.append(f"- {key}: {to_plain(item)}")
            else:
                lines.append(f"- {to_plain(value)}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"
