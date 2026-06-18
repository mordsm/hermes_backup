from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from ..db import session_scope
from ..life_agent.orchestrator import LifeAgent
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


def _stable_source_object_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"financial-followup:{digest}"


def _route_followups_to_life(report_kind: str, items: list, questions: list[str] | None = None) -> int:
    routed = 0
    questions = questions or []
    with session_scope() as session:
        life = LifeAgent(session)
        for index, action in enumerate(items):
            title = getattr(action, "title", str(action))
            reason = getattr(action, "reason", "")
            risk = getattr(action, "risk", "")
            missing_information = getattr(action, "missing_information", []) or []
            needs_professional_advice = bool(getattr(action, "needs_professional_advice", False))
            life.ingest_financial_followup(
                title=title,
                description=f"{reason}\nRisk: {risk}".strip(),
                source_object_id=_stable_source_object_id(report_kind, "manual", str(index), title, reason, risk),
                metadata={
                    "report_kind": report_kind,
                    "kind": "manual_approval",
                    "missing_information": missing_information,
                    "needs_professional_advice": needs_professional_advice,
                },
            )
            routed += 1

        for index, question in enumerate(questions):
            life.ingest_financial_followup(
                title=f"Answer finance question: {question}",
                description=question,
                source_object_id=_stable_source_object_id(report_kind, "question", str(index), question),
                metadata={
                    "report_kind": report_kind,
                    "kind": "question",
                },
            )
            routed += 1

        session.commit()
    return routed



@financial_app.command("weekly")
def weekly(
    input_file: str | None = typer.Option(None, help="Legacy JSON input with budgets/cashflow/positions/starting_balance"),
    data_path: str | None = typer.Option(None, help="Path to a JSON bundle or a CSV export directory"),
    route_to_life: bool = typer.Option(True, "--route-to-life/--no-route-to-life", help="Create life-agent follow-up tasks from manual approvals and questions"),
):
    agent = FinancialAgent()
    bundle = _load_bundle(data_path)
    if bundle is not None:
        starting_balance = 0.0
        report = agent.weekly_short_alerts_from_bundle(bundle, starting_balance)
        if route_to_life:
            _route_followups_to_life("weekly", report.manual_approval_actions, report.questions_for_moshe)
        typer.echo(json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str))
        return

    data = _load_json(input_file)
    profile = IntakeProfile(**data.get("profile", {}))
    budgets = [BudgetCategory(**item) for item in data.get("budgets", [])]
    cashflow_items = [CashflowItem(date=datetime.fromisoformat(item["date"]).date(), amount=item["amount"], label=item["label"], kind=item["kind"]) for item in data.get("cashflow_items", [])]
    positions = [AssetPosition(**item) for item in data.get("positions", [])]
    bundle = agent.weekly_short_alerts(profile, budgets, cashflow_items, positions, data.get("starting_balance", 0.0))
    if route_to_life:
        _route_followups_to_life("weekly", bundle.manual_approval_actions, bundle.questions_for_moshe)
    typer.echo(json.dumps(to_plain(bundle), ensure_ascii=False, indent=2, default=str))


@financial_app.command("monthly")
def monthly(
    input_file: str | None = typer.Option(None, help="Legacy JSON input with budgets/cashflow/positions/starting_balance"),
    data_path: str | None = typer.Option(None, help="Path to a JSON bundle or a CSV export directory"),
    route_to_life: bool = typer.Option(True, "--route-to-life/--no-route-to-life", help="Create life-agent follow-up tasks from manual approvals and questions"),
):
    agent = FinancialAgent()
    bundle = _load_bundle(data_path)
    if bundle is not None:
        report = agent.monthly_full_report_from_bundle(bundle, 0.0)
        if route_to_life:
            _route_followups_to_life("monthly", report.manual_approval_actions, report.questions_for_moshe)
        typer.echo(MonthlyReportGenerator().render_markdown(report))
        return

    data = _load_json(input_file)
    profile = IntakeProfile(**data.get("profile", {}))
    budgets = [BudgetCategory(**item) for item in data.get("budgets", [])]
    cashflow_items = [CashflowItem(date=datetime.fromisoformat(item["date"]).date(), amount=item["amount"], label=item["label"], kind=item["kind"]) for item in data.get("cashflow_items", [])]
    positions = [AssetPosition(**item) for item in data.get("positions", [])]
    report = agent.monthly_full_report(profile, budgets, cashflow_items, positions, data.get("starting_balance", 0.0))
    if route_to_life:
        _route_followups_to_life("monthly", report.manual_approval_actions, report.questions_for_moshe)
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
