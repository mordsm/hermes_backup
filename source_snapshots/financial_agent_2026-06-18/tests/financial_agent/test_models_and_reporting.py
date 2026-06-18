from task_reminder.app.financial_agent.models import FactItem, MonthlyReport, RecommendationItem, ConfidenceLevel, RiskItem, AlertSeverity, to_plain
from task_reminder.app.financial_agent.monthly_report import MonthlyReportGenerator


def test_monthly_report_serializes_with_expected_sections():
    report = MonthlyReport(
        headline="Monthly financial report",
        facts=[FactItem(text="Income detected", source="bank")],
        recommendations=[RecommendationItem(title="Review spending", reason="Budget exceeded", risk="Overspending", confidence_level=ConfidenceLevel.HIGH)],
        risks=[RiskItem(title="Low liquidity", detail="Projected low balance", severity=AlertSeverity.WARNING)],
    )
    plain = to_plain(report)
    assert plain["headline"] == "Monthly financial report"
    assert plain["facts"][0]["text"] == "Income detected"
    md = MonthlyReportGenerator().render_markdown(report)
    assert "## Facts" in md
    assert "## Recommendations" in md
    assert "## Risks" in md
