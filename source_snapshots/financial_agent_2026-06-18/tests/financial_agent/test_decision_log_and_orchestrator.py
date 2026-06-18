from datetime import date

from task_reminder.app.financial_agent.decision_log import DecisionLog
from task_reminder.app.financial_agent.models import AssetPosition, BudgetCategory, CashflowItem, IntakeProfile
from task_reminder.app.financial_agent.orchestrator import FinancialAgent


def test_decision_log_writes_entries(tmp_path):
    path = tmp_path / "decision_log.jsonl"
    log = DecisionLog(path)
    entry = log.add("budget", "alert", "Budget overrun detected", {"category": "Food"})
    assert entry.module == "budget"
    assert path.exists()
    assert path.read_text(encoding="utf-8").strip()


def test_orchestrator_generates_weekly_and_monthly_outputs():
    agent = FinancialAgent()
    profile = IntakeProfile(income_sources=["salary"], accounts=["checking"], recurring_expenses=["rent"], monthly_obligations=["rent"], risk_tolerance="medium", emergency_reserve_target=20000)
    budgets = [BudgetCategory(name="Food", limit=1000, spent=1200)]
    cashflow = [CashflowItem(date=date(2026, 6, 20), amount=-1200, label="rent", kind="expense")]
    positions = [AssetPosition(name="Index Fund", value=50000, weight_target=0.6)]
    weekly = agent.weekly_short_alerts(profile, budgets, cashflow, positions, starting_balance=100)
    monthly = agent.monthly_full_report(profile, budgets, cashflow, positions, starting_balance=100)
    assert weekly.weekly_alerts
    assert weekly.manual_approval_actions
    assert monthly.recommendations
    assert monthly.questions_for_moshe
