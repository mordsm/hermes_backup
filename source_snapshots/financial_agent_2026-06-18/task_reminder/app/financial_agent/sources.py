from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Protocol

from .budget_monitor import BudgetMonitor
from .ingestion import DataIngestionModule
from .models import (
    AssetPosition,
    BudgetCategory,
    CashflowItem,
    IntakeProfile,
    LiabilityPosition,
    Transaction,
)


@dataclass(slots=True)
class FinancialDataBundle:
    profile: IntakeProfile = field(default_factory=IntakeProfile)
    budgets: list[BudgetCategory] = field(default_factory=list)
    cashflow_items: list[CashflowItem] = field(default_factory=list)
    positions: list[AssetPosition] = field(default_factory=list)
    liabilities: list[LiabilityPosition] = field(default_factory=list)
    transactions: list[Transaction] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FinancialDataSource(Protocol):
    def load(self) -> FinancialDataBundle:
        ...


def _ensure_tzaware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _ensure_tzaware(value)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return _ensure_tzaware(parsed)
    raise TypeError(f'Unsupported datetime value: {value!r}')


def _parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return _ensure_tzaware(value).date()
    if isinstance(value, str):
        if 'T' in value:
            return _parse_datetime(value).date()
        return date.fromisoformat(value)
    raise TypeError(f'Unsupported date value: {value!r}')


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))


class JsonFinancialDataSource:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> FinancialDataBundle:
        payload = _read_json(self.path)
        return self._bundle_from_payload(payload)

    def _bundle_from_payload(self, payload: dict[str, Any]) -> FinancialDataBundle:
        profile = IntakeProfile(**payload.get('profile', {}))
        budgets = [BudgetCategory(**item) for item in payload.get('budgets', [])]
        cashflow_items = [
            CashflowItem(
                date=_parse_date(item['date']),
                amount=float(item['amount']),
                label=str(item['label']),
                kind=str(item['kind']),
            )
            for item in payload.get('cashflow_items', [])
        ]
        positions = [AssetPosition(**item) for item in payload.get('positions', [])]
        liabilities = [LiabilityPosition(**item) for item in payload.get('liabilities', [])]
        transactions = DataIngestionModule().ingest_transactions(payload.get('transactions', [])).transactions
        metadata = {k: v for k, v in payload.items() if k not in {'profile', 'budgets', 'cashflow_items', 'positions', 'liabilities', 'transactions'}}
        return FinancialDataBundle(
            profile=profile,
            budgets=budgets,
            cashflow_items=cashflow_items,
            positions=positions,
            liabilities=liabilities,
            transactions=transactions,
            metadata=metadata,
        )


class CsvFinancialDataSource:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> FinancialDataBundle:
        if self.path.is_file():
            return self._load_transactions_file(self.path)

        profile = self._load_profile()
        budgets = self._load_budgets()
        cashflow_items = self._load_cashflow_items()
        positions = self._load_positions()
        liabilities = self._load_liabilities()
        transactions = self._load_transactions()
        metadata = {'source_dir': str(self.path)}
        return FinancialDataBundle(
            profile=profile,
            budgets=budgets,
            cashflow_items=cashflow_items,
            positions=positions,
            liabilities=liabilities,
            transactions=transactions,
            metadata=metadata,
        )

    def _load_profile(self) -> IntakeProfile:
        profile_path = self.path / 'profile.json'
        if profile_path.exists():
            return IntakeProfile(**_read_json(profile_path))
        return IntakeProfile()

    def _load_budgets(self) -> list[BudgetCategory]:
        csv_path = self.path / 'budgets.csv'
        if not csv_path.exists():
            return []
        return [BudgetCategory(name=row['name'], limit=float(row['limit']), spent=float(row.get('spent', 0) or 0)) for row in _read_csv_rows(csv_path)]

    def _load_cashflow_items(self) -> list[CashflowItem]:
        csv_path = self.path / 'cashflow.csv'
        if not csv_path.exists():
            csv_path = self.path / 'cashflow_items.csv'
        if not csv_path.exists():
            return []
        items: list[CashflowItem] = []
        for row in _read_csv_rows(csv_path):
            items.append(
                CashflowItem(
                    date=_parse_date(row['date']),
                    amount=float(row['amount']),
                    label=row['label'],
                    kind=row['kind'],
                )
            )
        return items

    def _load_positions(self) -> list[AssetPosition]:
        csv_path = self.path / 'positions.csv'
        if not csv_path.exists():
            return []
        items: list[AssetPosition] = []
        for row in _read_csv_rows(csv_path):
            items.append(
                AssetPosition(
                    name=row['name'],
                    value=float(row['value']),
                    asset_class=row.get('asset_class') or 'unknown',
                    weight_target=float(row['weight_target']) if row.get('weight_target') not in (None, '') else None,
                    volatility_note=row.get('volatility_note') or None,
                )
            )
        return items

    def _load_liabilities(self) -> list[LiabilityPosition]:
        csv_path = self.path / 'liabilities.csv'
        if not csv_path.exists():
            return []
        items: list[LiabilityPosition] = []
        for row in _read_csv_rows(csv_path):
            due_date = _parse_date(row['due_date']) if row.get('due_date') else None
            interest_rate = float(row['interest_rate']) if row.get('interest_rate') not in (None, '') else None
            items.append(
                LiabilityPosition(
                    name=row['name'],
                    balance=float(row['balance']),
                    due_date=due_date,
                    interest_rate=interest_rate,
                )
            )
        return items

    def _load_transactions(self) -> list[Transaction]:
        csv_path = self.path / 'transactions.csv'
        if not csv_path.exists():
            return []
        rows = []
        for row in _read_csv_rows(csv_path):
            payload = {
                'posted_at': row['posted_at'],
                'description': row['description'],
                'amount': float(row['amount']),
                'currency': row.get('currency') or 'ILS',
                'category': row.get('category') or None,
                'source': row.get('source') or 'csv',
                'recurring': str(row.get('recurring', '')).lower() in {'1', 'true', 'yes', 'y'},
            }
            rows.append(payload)
        return DataIngestionModule().ingest_transactions(rows).transactions

    def _load_transactions_file(self, path: Path) -> FinancialDataBundle:
        rows = _read_csv_rows(path)
        transactions = DataIngestionModule().ingest_transactions([
            {
                'posted_at': row.get('posted_at') or datetime.now(timezone.utc).isoformat(),
                'description': row.get('description', ''),
                'amount': float(row.get('amount', 0) or 0),
                'currency': row.get('currency') or 'ILS',
                'category': row.get('category') or None,
                'source': row.get('source') or 'csv',
                'recurring': str(row.get('recurring', '')).lower() in {'1', 'true', 'yes', 'y'},
            }
            for row in rows
        ]).transactions
        return FinancialDataBundle(transactions=transactions, metadata={'source_file': str(path)})


class AutoFinancialDataSource:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> FinancialDataBundle:
        if self.path.is_dir():
            if (self.path / 'financial.json').exists():
                return JsonFinancialDataSource(self.path / 'financial.json').load()
            if (self.path / 'bundle.json').exists():
                return JsonFinancialDataSource(self.path / 'bundle.json').load()
            return CsvFinancialDataSource(self.path).load()
        if self.path.suffix.lower() == '.json':
            return JsonFinancialDataSource(self.path).load()
        if self.path.suffix.lower() == '.csv':
            return CsvFinancialDataSource(self.path).load()
        raise ValueError(f'Unsupported financial data source: {self.path}')
