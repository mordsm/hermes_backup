from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from .monthly_report import MonthlyReportGenerator
from .models import AssetPosition, BudgetCategory, CashflowItem, IntakeProfile, MonthlyReport, to_plain
from .orchestrator import FinancialAgent
from .sources import AutoFinancialDataSource

financial_app = typer.Typer(help="Read-only financial management agent")


def _load_json(path: str | None) -> dict:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_bundle(data_path: str | None):
    if not data_path:
        return None
    return AutoFinancialDataSource(data_path).load()


@financial_app.command("weekly")
def weekly(
    input_file: str | None = typer.Option(None, help="Legacy JSON input with budgets/cashflow/positions/starting_balance"),
    data_path: str | None = typer.Option(None, help="Path to a JSON bundle or a CSV export directory"),
):
    agent = FinancialAgent()
    bundle = _load_bundle(data_path)
    if bundle is not None:
        starting_balance = 0.0
        report = agent.weekly_short_alerts_from_bundle(bundle, starting_balance)
        typer.echo(json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str))
        return

    data = _load_json(input_file)
    profile = IntakeProfile(**data.get("profile", {}))
    budgets = [BudgetCategory(**item) for item in data.get("budgets", [])]
    cashflow_items = [CashflowItem(date=datetime.fromisoformat(item["date"]).date(), amount=item["amount"], label=item["label"], kind=item["kind"]) for item in data.get("cashflow_items", [])]
    positions = [AssetPosition(**item) for item in data.get("positions", [])]
    bundle = agent.weekly_short_alerts(profile, budgets, cashflow_items, positions, data.get("starting_balance", 0.0))
    typer.echo(json.dumps(to_plain(bundle), ensure_ascii=False, indent=2, default=str))


@financial_app.command("monthly")
def monthly(
    input_file: str | None = typer.Option(None, help="Legacy JSON input with budgets/cashflow/positions/starting_balance"),
    data_path: str | None = typer.Option(None, help="Path to a JSON bundle or a CSV export directory"),
):
    agent = FinancialAgent()
    bundle = _load_bundle(data_path)
    if bundle is not None:
        report = agent.monthly_full_report_from_bundle(bundle, 0.0)
        typer.echo(MonthlyReportGenerator().render_markdown(report))
        return

    data = _load_json(input_file)
    profile = IntakeProfile(**data.get("profile", {}))
    budgets = [BudgetCategory(**item) for item in data.get("budgets", [])]
    cashflow_items = [CashflowItem(date=datetime.fromisoformat(item["date"]).date(), amount=item["amount"], label=item["label"], kind=item["kind"]) for item in data.get("cashflow_items", [])]
    positions = [AssetPosition(**item) for item in data.get("positions", [])]
    report = agent.monthly_full_report(profile, budgets, cashflow_items, positions, data.get("starting_balance", 0.0))
    typer.echo(MonthlyReportGenerator().render_markdown(report))


@financial_app.command("questions")
def questions(
    input_file: str | None = typer.Option(None, help="Legacy JSON input with profile"),
    data_path: str | None = typer.Option(None, help="Path to a JSON bundle or CSV export directory"),
):
    agent = FinancialAgent()
    bundle = _load_bundle(data_path)
    if bundle is not None:
        typer.echo(json.dumps(agent.questions_for_moshe(bundle.profile), ensure_ascii=False, indent=2))
        return

    data = _load_json(input_file)
    profile = IntakeProfile(**data.get("profile", {}))
    typer.echo(json.dumps(agent.questions_for_moshe(profile), ensure_ascii=False, indent=2))
