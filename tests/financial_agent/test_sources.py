from __future__ import annotations

import json
from datetime import date

from task_reminder.app.financial_agent.orchestrator import FinancialAgent
from task_reminder.app.financial_agent.sources import CsvFinancialDataSource, JsonFinancialDataSource


def test_json_source_loads_financial_bundle(tmp_path):
    payload = {
        "profile": {
            "income_sources": ["salary"],
            "accounts": ["checking"],
            "recurring_expenses": ["rent"],
            "monthly_obligations": ["rent"],
            "risk_tolerance": "medium",
            "emergency_reserve_target": 15000,
        },
        "budgets": [{"name": "Food", "limit": 1200, "spent": 900}],
        "cashflow_items": [
            {
                "date": "2026-06-20",
                "amount": -2500,
                "label": "rent",
                "kind": "expense",
            }
        ],
        "transactions": [
            {
                "posted_at": "2026-06-19T08:30:00+03:00",
                "description": "Salary",
                "amount": 12000,
                "currency": "ILS",
                "category": "income",
                "source": "bank",
                "recurring": True,
            }
        ],
        "positions": [{"name": "Index Fund", "value": 50000, "asset_class": "equity"}],
    }
    path = tmp_path / "financial.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    bundle = JsonFinancialDataSource(path).load()

    assert bundle.profile.income_sources == ["salary"]
    assert bundle.budgets[0].name == "Food"
    assert bundle.cashflow_items[0].date == date(2026, 6, 20)
    assert bundle.transactions[0].posted_at.tzinfo is not None
    assert bundle.positions[0].name == "Index Fund"


def test_csv_source_loads_transactions_and_related_records(tmp_path):
    (tmp_path / "profile.json").write_text(
        json.dumps(
            {
                "income_sources": ["salary"],
                "accounts": ["checking"],
                "recurring_expenses": ["rent"],
                "monthly_obligations": ["rent"],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "budgets.csv").write_text("name,limit,spent\nFood,1000,800\nRent,3000,3000\n", encoding="utf-8")
    (tmp_path / "transactions.csv").write_text(
        "posted_at,description,amount,currency,category,source,recurring\n2026-06-20T08:30:00+03:00,Salary,12000,ILS,income,bank,true\n2026-06-21T09:00:00+03:00,Groceries,-350,ILS,food,bank,false\n",
        encoding="utf-8",
    )
    (tmp_path / "positions.csv").write_text(
        "name,value,asset_class,weight_target,volatility_note\nIndex Fund,50000,equity,0.6,medium\n",
        encoding="utf-8",
    )

    bundle = CsvFinancialDataSource(tmp_path).load()

    assert bundle.profile.accounts == ["checking"]
    assert len(bundle.budgets) == 2
    assert bundle.transactions[0].posted_at.tzinfo is not None
    assert bundle.transactions[0].recurring is True
    assert bundle.positions[0].asset_class == "equity"


def test_agent_can_report_from_real_source_directory(tmp_path):
    (tmp_path / "profile.json").write_text(
        json.dumps(
            {
                "income_sources": ["salary"],
                "accounts": ["checking"],
                "recurring_expenses": ["rent"],
                "monthly_obligations": ["rent"],
                "risk_tolerance": "medium",
                "emergency_reserve_target": 10000,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "budgets.csv").write_text("name,limit,spent\nFood,1000,800\n", encoding="utf-8")
    (tmp_path / "transactions.csv").write_text(
        "posted_at,description,amount,currency,category,source,recurring\n2026-06-20T08:30:00+03:00,Salary,12000,ILS,income,bank,true\n",
        encoding="utf-8",
    )
    agent = FinancialAgent()

    report = agent.monthly_full_report_from_source(tmp_path)

    assert report.facts
    assert report.budget_summary["categories"] == ["Food"]
    assert report.questions_for_moshe == []
