from task_reminder.app.financial_agent.coordinator import CoordinatorInterface
from task_reminder.app.financial_agent.investment_watcher import InvestmentWatcher
from task_reminder.app.financial_agent.models import AssetPosition, MonthlyReport, FactItem, RiskItem, RecommendationItem, ApprovalAction, ConfidenceLevel, AlertSeverity


def test_investment_watcher_produces_manual_review_recommendation():
    result = InvestmentWatcher().inspect([AssetPosition(name="Index Fund", value=50000, weight_target=0.6)])
    assert result.recommendations
    assert result.recommendations[0].needs_professional_advice is True
    assert result.risks


def test_coordinator_message_is_small_and_actionable():
    report = MonthlyReport(
        headline="Monthly financial report",
        facts=[FactItem(text="Balance stable")],
        risks=[RiskItem(title="Low liquidity", detail="Projected low balance", severity=AlertSeverity.WARNING)],
        recommendations=[RecommendationItem(title="Reduce discretionary spend", reason="Overspend", risk="Cash pressure", confidence_level=ConfidenceLevel.MEDIUM)],
        manual_approval_actions=[ApprovalAction(title="Review budget", reason="Spending spike", risk="Cash pressure", confidence_level=ConfidenceLevel.MEDIUM)],
    )
    message = CoordinatorInterface().summarize_for_self_management(report)
    assert message.topic == "financial_status"
    assert message.priority == "high"
    assert message.next_actions
    assert message.manual_approvals_needed
