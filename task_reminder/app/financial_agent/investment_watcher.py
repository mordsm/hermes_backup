from __future__ import annotations

from .models import AlertSeverity, AssetPosition, AssumptionItem, ConfidenceLevel, FactItem, InvestmentResult, MissingInfoItem, RecommendationItem, RiskItem


class InvestmentWatcher:
    def inspect(self, positions: list[AssetPosition]) -> InvestmentResult:
        facts = [FactItem(text=f"{p.name}: value {p.value}", source="investments") for p in positions]
        risks: list[RiskItem] = []
        recommendations: list[RecommendationItem] = []
        for position in positions:
            if position.weight_target is not None and position.value > 0:
                risks.append(RiskItem(title=f"Allocation watch: {position.name}", detail=f"Target weight noted at {position.weight_target}", severity=AlertSeverity.INFO, confidence=ConfidenceLevel.MEDIUM))
                recommendations.append(RecommendationItem(title=f"Consider manual review of {position.name}", reason="Allocation may have drifted", risk="Rebalancing without context may create tax or timing costs", confidence_level=ConfidenceLevel.MEDIUM, missing_information=["Current portfolio weights", "Tax implications", "Liquidity needs"], needs_professional_advice=True, manual_approval_required=True, next_step="Review with Moshe or a professional before any change"))
        return InvestmentResult(facts=facts, assumptions=[AssumptionItem(text="Positions are current as of the latest import")], missing_information=[MissingInfoItem(text="Benchmark and tax context are not yet connected", reason="Limits accuracy of advice")], recommendations=recommendations, risks=risks)
