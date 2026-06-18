from datetime import date

from task_reminder.app.financial_agent.budget_monitor import BudgetMonitor
from task_reminder.app.financial_agent.cashflow_planner import CashflowPlanner
from task_reminder.app.financial_agent.models import BudgetCategory, CashflowItem


def test_budget_monitor_detects_overrun():
    result = BudgetMonitor().evaluate([BudgetCategory(name="Food", limit=1000, spent=1200)])
    assert result.risks
    assert result.recommendations
    assert result.risks[0].title == "Budget overrun in Food"


def test_cashflow_planner_flags_negative_projection():
    items = [
        CashflowItem(date=date(2026, 6, 20), amount=-1200, label="rent", kind="expense"),
        CashflowItem(date=date(2026, 6, 25), amount=500, label="income", kind="income"),
    ]
    result = CashflowPlanner().project(starting_balance=100, items=items)
    assert result.projected_balance == -600
    assert result.risks
    assert result.recommendations
