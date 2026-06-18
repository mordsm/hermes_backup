from __future__ import annotations

from .models import AlertBundle, ApprovalAction, AlertSeverity, RecommendationItem, RiskItem, WeeklyAlert


class RiskAndAlertModule:
    def build_weekly_alerts(self, risks: list[RiskItem], recommendations: list[RecommendationItem]) -> AlertBundle:
        weekly_alerts: list[WeeklyAlert] = []
        manual_actions: list[ApprovalAction] = []
        questions: list[str] = []

        if risks:
            headline = "Financial risks require review" if any(r.severity == AlertSeverity.CRITICAL for r in risks) else "Financial status update"
            weekly_alerts.append(WeeklyAlert(headline=headline, summary=self._summarize(risks), severity=self._max_severity(risks), risks=risks))

        for rec in recommendations:
            manual_actions.append(ApprovalAction(title=rec.title, reason=rec.reason, risk=rec.risk, confidence_level=rec.confidence_level, missing_information=rec.missing_information, needs_professional_advice=rec.needs_professional_advice))
            if rec.kind.value == "question" or rec.missing_information:
                questions.extend(rec.missing_information)

        return AlertBundle(weekly_alerts=weekly_alerts, manual_approval_actions=manual_actions, questions_for_moshe=questions, risks=risks)

    def _summarize(self, risks: list[RiskItem]) -> str:
        titles = ", ".join(r.title for r in risks[:3])
        return f"Key issues: {titles}" if titles else "No material risks detected"

    def _max_severity(self, risks: list[RiskItem]) -> AlertSeverity:
        order = {AlertSeverity.INFO: 0, AlertSeverity.WARNING: 1, AlertSeverity.CRITICAL: 2}
        return max((r.severity for r in risks), key=lambda sev: order[sev]) if risks else AlertSeverity.INFO
