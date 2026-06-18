from __future__ import annotations

from .models import CoordinatorMessage, MonthlyReport


class CoordinatorInterface:
    def summarize_for_self_management(self, report: MonthlyReport) -> CoordinatorMessage:
        facts = [item.text for item in report.facts[:5]]
        risks = [item.title for item in report.risks[:5]]
        next_actions = [item.title for item in report.recommendations[:5]]
        manual = [item.title for item in report.manual_approval_actions[:5]]
        priority = "high" if risks else "medium"
        return CoordinatorMessage(topic="financial_status", priority=priority, facts=facts, risks=risks, next_actions=next_actions, manual_approvals_needed=manual)
