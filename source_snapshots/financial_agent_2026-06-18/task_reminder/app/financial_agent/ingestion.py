from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import IngestionResult, Transaction


class DataIngestionModule:
    def ingest_transactions(self, raw_items: list[dict[str, Any]]) -> IngestionResult:
        transactions: list[Transaction] = []
        warnings: list[str] = []
        recurring_items: list[str] = []

        for item in raw_items:
            try:
                posted_at = item.get("posted_at")
                if isinstance(posted_at, str):
                    posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                elif posted_at is None:
                    posted_at = datetime.now(timezone.utc)
                amount = float(item["amount"])
                txn = Transaction(
                    posted_at=posted_at,
                    description=str(item.get("description", "")),
                    amount=amount,
                    currency=str(item.get("currency", "ILS")),
                    category=item.get("category"),
                    source=str(item.get("source", "manual")),
                    recurring=bool(item.get("recurring", False)),
                    metadata={k: v for k, v in item.items() if k not in {"posted_at", "description", "amount", "currency", "category", "source", "recurring"}},
                )
                transactions.append(txn)
                if txn.recurring:
                    recurring_items.append(txn.description)
            except Exception as exc:  # pragma: no cover - defensive parsing path
                warnings.append(f"Could not ingest item: {exc}")

        return IngestionResult(transactions=transactions, recurring_items=recurring_items, warnings=warnings)
