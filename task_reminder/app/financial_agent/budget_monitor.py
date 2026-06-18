from __future__ import annotations

from .models import AlertSeverity, AssumptionItem, BudgetCategory, BudgetResult, FactItem, MissingInfoItem, RecommendationItem, RiskItem, ConfidenceLevel


class BudgetMonitor:
    def evaluate(self, categories: list[BudgetCategory]) -> BudgetResult:
        facts: list[FactItem] = []
        recommendations: list[RecommendationItem] = []
        risks: list[RiskItem] = []

        for category in categories:
            facts.append(FactItem(text=f"{category.name}: spent {category.spent} of {category.limit}", source="budget"))
            if category.limit <= 0:
                continue
            ratio = category.spent / category.limit
            if ratio >= 1:
                risks.append(RiskItem(title=f"Budget overrun in {category.name}", detail=f"Spent {category.spent} vs limit {category.limit}", severity=AlertSeverity.CRITICAL, confidence=ConfidenceLevel.HIGH))
                recommendations.append(RecommendationItem(title=f"Review {category.name} spending", reason="Category is over budget", risk="Further overspending may strain cashflow", confidence_level=ConfidenceLevel.HIGH, missing_information=["Which transactions were essential?"], needs_professional_advice=False, manual_approval_required=True, next_step="Review and approve corrective action manually"))
            elif ratio >= 0.9:
                risks.append(RiskItem(title=f"Approaching limit in {category.name}", detail=f"Spent {category.spent} vs limit {category.limit}", severity=AlertSeverity.WARNING, confidence=ConfidenceLevel.MEDIUM))

        return BudgetResult(facts=facts, assumptions=[AssumptionItem(text="Categories reflect current monthly budget limits")], missing_information=[MissingInfoItem(text="Category-level transaction mapping may be incomplete", reason="Needed for higher-confidence analysis")], recommendations=recommendations, risks=risks)
