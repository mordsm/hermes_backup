from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from enum import Enum
from typing import Any


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class RecommendationKind(str, Enum):
    MANUAL_APPROVAL = "manual_approval"
    ADVISORY = "advisory"
    QUESTION = "question"


@dataclass(slots=True)
class FactItem:
    text: str
    source: str = "unknown"
    timestamp: datetime | None = None


@dataclass(slots=True)
class AssumptionItem:
    text: str
    source: str = "inferred"


@dataclass(slots=True)
class MissingInfoItem:
    text: str
    reason: str | None = None


@dataclass(slots=True)
class RiskItem:
    title: str
    detail: str
    severity: AlertSeverity = AlertSeverity.WARNING
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


@dataclass(slots=True)
class RecommendationItem:
    title: str
    reason: str
    risk: str
    confidence_level: ConfidenceLevel
    missing_information: list[str] = field(default_factory=list)
    needs_professional_advice: bool = False
    manual_approval_required: bool = True
    next_step: str = "Review manually"
    kind: RecommendationKind = RecommendationKind.MANUAL_APPROVAL


@dataclass(slots=True)
class ApprovalAction:
    title: str
    reason: str
    risk: str
    confidence_level: ConfidenceLevel
    missing_information: list[str] = field(default_factory=list)
    needs_professional_advice: bool = False


@dataclass(slots=True)
class WeeklyAlert:
    headline: str
    summary: str
    severity: AlertSeverity = AlertSeverity.INFO
    facts: list[FactItem] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)
    manual_approval_actions: list[ApprovalAction] = field(default_factory=list)


@dataclass(slots=True)
class MonthlyReport:
    headline: str
    facts: list[FactItem] = field(default_factory=list)
    assumptions: list[AssumptionItem] = field(default_factory=list)
    missing_information: list[MissingInfoItem] = field(default_factory=list)
    recommendations: list[RecommendationItem] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)
    manual_approval_actions: list[ApprovalAction] = field(default_factory=list)
    questions_for_moshe: list[str] = field(default_factory=list)
    budget_summary: dict[str, Any] = field(default_factory=dict)
    cashflow_summary: dict[str, Any] = field(default_factory=dict)
    investment_summary: dict[str, Any] = field(default_factory=dict)
    decision_log_highlights: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DecisionLogEntry:
    timestamp: datetime
    module: str
    kind: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CoordinatorMessage:
    topic: str
    priority: str
    facts: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    manual_approvals_needed: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Transaction:
    posted_at: datetime
    description: str
    amount: float
    currency: str = "ILS"
    category: str | None = None
    source: str = "manual"
    recurring: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BudgetCategory:
    name: str
    limit: float
    spent: float = 0.0


@dataclass(slots=True)
class CashflowItem:
    date: date
    amount: float
    label: str
    kind: str


@dataclass(slots=True)
class AssetPosition:
    name: str
    value: float
    asset_class: str = "unknown"
    weight_target: float | None = None
    volatility_note: str | None = None


@dataclass(slots=True)
class LiabilityPosition:
    name: str
    balance: float
    due_date: date | None = None
    interest_rate: float | None = None


@dataclass(slots=True)
class IntakeProfile:
    income_sources: list[str] = field(default_factory=list)
    accounts: list[str] = field(default_factory=list)
    recurring_expenses: list[str] = field(default_factory=list)
    debts: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    liabilities: list[str] = field(default_factory=list)
    monthly_obligations: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    risk_tolerance: str | None = None
    emergency_reserve_target: float | None = None
    reporting_preferences: dict[str, Any] = field(default_factory=dict)
    permission_boundaries: list[str] = field(default_factory=lambda: [
        "no transfers",
        "no trading",
        "no bank instructions",
        "no irreversible decisions",
    ])


@dataclass(slots=True)
class IngestionResult:
    transactions: list[Transaction] = field(default_factory=list)
    recurring_items: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BudgetResult:
    facts: list[FactItem] = field(default_factory=list)
    assumptions: list[AssumptionItem] = field(default_factory=list)
    missing_information: list[MissingInfoItem] = field(default_factory=list)
    recommendations: list[RecommendationItem] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)


@dataclass(slots=True)
class CashflowResult:
    facts: list[FactItem] = field(default_factory=list)
    assumptions: list[AssumptionItem] = field(default_factory=list)
    missing_information: list[MissingInfoItem] = field(default_factory=list)
    recommendations: list[RecommendationItem] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)
    projected_balance: float | None = None


@dataclass(slots=True)
class InvestmentResult:
    facts: list[FactItem] = field(default_factory=list)
    assumptions: list[AssumptionItem] = field(default_factory=list)
    missing_information: list[MissingInfoItem] = field(default_factory=list)
    recommendations: list[RecommendationItem] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)


@dataclass(slots=True)
class AlertBundle:
    weekly_alerts: list[WeeklyAlert] = field(default_factory=list)
    manual_approval_actions: list[ApprovalAction] = field(default_factory=list)
    questions_for_moshe: list[str] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)


def to_plain(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if dataclass_is_instance(obj):
        return _plain_dataclass(obj)
    if isinstance(obj, list):
        return [to_plain(item) for item in obj]
    if isinstance(obj, dict):
        return {key: to_plain(value) for key, value in obj.items()}
    if isinstance(obj, Enum):
        return obj.value
    return obj


def _plain_dataclass(obj: Any) -> Any:
    data = asdict(obj)
    return {key: to_plain(value) for key, value in data.items()}


def dataclass_is_instance(obj: Any) -> bool:
    return hasattr(obj, "__dataclass_fields__") and not isinstance(obj, type)
