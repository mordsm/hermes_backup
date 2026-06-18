from __future__ import annotations

from datetime import date

from .models import AlertSeverity, AssumptionItem, CashflowItem, CashflowResult, ConfidenceLevel, FactItem, MissingInfoItem, RecommendationItem, RiskItem


class CashflowPlanner:
    def project(self, starting_balance: float, items: list[CashflowItem]) -> CashflowResult:
        projected = starting_balance
        facts: list[FactItem] = [FactItem(text=f"Starting balance: {starting_balance}", source="cashflow")]
        ordered = sorted(items, key=lambda item: item.date)
        for item in ordered:
            projected += item.amount
            facts.append(FactItem(text=f"{item.kind} {item.label} on {item.date}: {item.amount}", source="cashflow"))

        risks: list[RiskItem] = []
        recommendations: list[RecommendationItem] = []
        if projected < 0:
            risks.append(RiskItem(title="Projected negative cash balance", detail=f"Projected ending balance {projected}", severity=AlertSeverity.CRITICAL, confidence=ConfidenceLevel.HIGH))
            recommendations.append(RecommendationItem(title="Review upcoming bills", reason="Projected balance falls below zero", risk="Possible missed payments or overdraft", confidence_level=ConfidenceLevel.HIGH, missing_information=["Exact timing of discretionary expenses", "Any flexible income sources"], needs_professional_advice=False, manual_approval_required=True, next_step="Approve manual spending reductions or timing changes"))
        elif projected < starting_balance * 0.2:
            risks.append(RiskItem(title="Low projected liquidity", detail=f"Projected ending balance {projected}", severity=AlertSeverity.WARNING, confidence=ConfidenceLevel.MEDIUM))

        return CashflowResult(facts=facts, assumptions=[AssumptionItem(text="All known cashflow items are included in the forecast")], missing_information=[MissingInfoItem(text="Unlisted recurring bills may exist", reason="Forecast may be optimistic")], recommendations=recommendations, risks=risks, projected_balance=projected)
