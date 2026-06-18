from __future__ import annotations

from pathlib import Path

from .budget_monitor import BudgetMonitor
from .cashflow_planner import CashflowPlanner
from .coordinator import CoordinatorInterface
from .decision_log import DecisionLog
from .investment_watcher import InvestmentWatcher
from .intake import IntakeModule
from .ingestion import DataIngestionModule
from .models import (
    AlertBundle,
    ApprovalAction,
    AssetPosition,
    BudgetCategory,
    CashflowItem,
    MonthlyReport,
    RiskItem,
    IntakeProfile,
)
from .monthly_report import MonthlyReportGenerator
from .risk_alerts import RiskAndAlertModule
from .sources import FinancialDataBundle, FinancialDataSource, AutoFinancialDataSource


class FinancialAgent:
    def __init__(self, decision_log: DecisionLog | None = None):
        self.intake = IntakeModule()
        self.ingestion = DataIngestionModule()
        self.budget_monitor = BudgetMonitor()
        self.cashflow_planner = CashflowPlanner()
        self.investment_watcher = InvestmentWatcher()
        self.risk_alerts = RiskAndAlertModule()
        self.report_generator = MonthlyReportGenerator()
        self.coordinator = CoordinatorInterface()
        self.decision_log = decision_log or DecisionLog()

    def weekly_short_alerts(self, profile: IntakeProfile, budgets: list[BudgetCategory], cashflow_items: list[CashflowItem], positions: list[AssetPosition], starting_balance: float = 0.0) -> AlertBundle:
        budget = self.budget_monitor.evaluate(budgets)
        cashflow = self.cashflow_planner.project(starting_balance, cashflow_items)
        investments = self.investment_watcher.inspect(positions)
        bundle = self.risk_alerts.build_weekly_alerts(budget.risks + cashflow.risks + investments.risks, budget.recommendations + cashflow.recommendations + investments.recommendations)
        self.decision_log.add("orchestrator", "weekly", "Weekly alerts generated", {"questions": bundle.questions_for_moshe})
        return bundle

    def monthly_full_report(self, profile: IntakeProfile, budgets: list[BudgetCategory], cashflow_items: list[CashflowItem], positions: list[AssetPosition], starting_balance: float = 0.0) -> MonthlyReport:
        budget = self.budget_monitor.evaluate(budgets)
        cashflow = self.cashflow_planner.project(starting_balance, cashflow_items)
        investments = self.investment_watcher.inspect(positions)
        combined_risks: list[RiskItem] = budget.risks + cashflow.risks + investments.risks
        combined_recommendations = budget.recommendations + cashflow.recommendations + investments.recommendations
        alert_bundle = self.risk_alerts.build_weekly_alerts(combined_risks, combined_recommendations)
        report = MonthlyReport(
            headline="Monthly financial report",
            facts=budget.facts + cashflow.facts + investments.facts,
            assumptions=budget.assumptions + cashflow.assumptions + investments.assumptions,
            missing_information=budget.missing_information + cashflow.missing_information + investments.missing_information,
            recommendations=combined_recommendations,
            risks=combined_risks,
            manual_approval_actions=alert_bundle.manual_approval_actions,
            questions_for_moshe=alert_bundle.questions_for_moshe,
            budget_summary={"categories": [c.name for c in budgets]},
            cashflow_summary={"projected_balance": cashflow.projected_balance},
            investment_summary={"positions": [p.name for p in positions]},
            decision_log_highlights=["Weekly and monthly analysis completed"],
        )
        self.decision_log.add("orchestrator", "monthly", "Monthly report generated", {"questions": report.questions_for_moshe})
        return report

    def weekly_short_alerts_from_bundle(self, bundle: FinancialDataBundle, starting_balance: float = 0.0) -> AlertBundle:
        return self.weekly_short_alerts(bundle.profile, bundle.budgets, bundle.cashflow_items, bundle.positions, starting_balance)

    def monthly_full_report_from_bundle(self, bundle: FinancialDataBundle, starting_balance: float = 0.0) -> MonthlyReport:
        return self.monthly_full_report(bundle.profile, bundle.budgets, bundle.cashflow_items, bundle.positions, starting_balance)

    def weekly_short_alerts_from_source(self, source: FinancialDataSource | str, starting_balance: float = 0.0) -> AlertBundle:
        data_source = source if hasattr(source, "load") else AutoFinancialDataSource(Path(source))
        return self.weekly_short_alerts_from_bundle(data_source.load(), starting_balance)

    def monthly_full_report_from_source(self, source: FinancialDataSource | str, starting_balance: float = 0.0) -> MonthlyReport:
        data_source = source if hasattr(source, "load") else AutoFinancialDataSource(Path(source))
        return self.monthly_full_report_from_bundle(data_source.load(), starting_balance)

    def questions_for_moshe(self, profile: IntakeProfile) -> list[str]:
        return self.intake.build_questions(profile)

    def manual_approval_actions(self, profile: IntakeProfile, budgets: list[BudgetCategory], cashflow_items: list[CashflowItem], positions: list[AssetPosition], starting_balance: float = 0.0) -> list[ApprovalAction]:
        bundle = self.weekly_short_alerts(profile, budgets, cashflow_items, positions, starting_balance)
        return bundle.manual_approval_actions

    def coordinator_message(self, report: MonthlyReport):
        return self.coordinator.summarize_for_self_management(report)
