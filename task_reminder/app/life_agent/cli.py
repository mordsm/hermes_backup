from __future__ import annotations

import json
from datetime import date, datetime

import typer

from ..connectors.google_calendar import GoogleCalendarConnector
from ..db import session_scope
from .models import to_plain
from .orchestrator import LifeAgent
from .reporting import render_life_report

life_app = typer.Typer(help="Separate life-management agent (Kanban, calendar, and recurring anchors)")


def _parse_dates(values: list[str] | None) -> set[date]:
    if not values:
        return set()
    return {date.fromisoformat(value) for value in values}


@life_app.command("seed-anchors")
def seed_anchors():
    with session_scope() as session:
        created = LifeAgent(session).seed_default_anchors()
        typer.echo(json.dumps({"created": [{"id": task.id, "title": task.title, "source_object_id": task.source_object_id} for task in created]}, ensure_ascii=False, indent=2, default=str))


@life_app.command("connect-calendar")
def connect_calendar():
    connector = GoogleCalendarConnector()
    creds = connector.authorize()
    if creds is None:
        typer.echo(json.dumps({"ok": False, "error": "Missing GOOGLE_CLIENT_SECRET_FILE or GOOGLE_TOKEN_FILE, or the secret file was not found."}, ensure_ascii=False, indent=2))
        raise typer.Exit(code=1)
    typer.echo(json.dumps({"ok": True, "message": "Google Calendar token saved."}, ensure_ascii=False, indent=2))


@life_app.command("sync-calendar")
def sync_calendar():
    with session_scope() as session:
        result = LifeAgent(session).sync_calendar()
        typer.echo(json.dumps(to_plain(result), ensure_ascii=False, indent=2, default=str))


@life_app.command("daily")
def daily(report_date: str | None = typer.Option(None, help="Date in YYYY-MM-DD format"), json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of markdown")):
    with session_scope() as session:
        day = date.fromisoformat(report_date) if report_date else None
        agent = LifeAgent(session)
        agent.generate_anchor_instances(horizon_days=2)
        report = agent.build_daily_report(day)
        if json_output:
            typer.echo(json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str))
            return
        typer.echo(render_life_report(report))


@life_app.command("weekly")
def weekly(report_date: str | None = typer.Option(None, help="Date in YYYY-MM-DD format"), json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of markdown")):
    with session_scope() as session:
        day = date.fromisoformat(report_date) if report_date else None
        agent = LifeAgent(session)
        agent.generate_anchor_instances(horizon_days=9)
        report = agent.build_weekly_report(day)
        if json_output:
            typer.echo(json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str))
            return
        typer.echo(render_life_report(report))


@life_app.command("monthly")
def monthly(
    report_date: str | None = typer.Option(None, help="Date in YYYY-MM-DD format"),
    holiday_date: list[str] | None = typer.Option(None, "--holiday-date", help="Holiday-like dates that should move the month-end checkpoint back one business day"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of markdown"),
):
    with session_scope() as session:
        day = date.fromisoformat(report_date) if report_date else None
        agent = LifeAgent(session)
        agent.generate_anchor_instances(horizon_days=40, holiday_dates=_parse_dates(holiday_date))
        report = agent.build_monthly_report(day, holiday_dates=_parse_dates(holiday_date))
        if json_output:
            typer.echo(json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str))
            return
        typer.echo(render_life_report(report))


@life_app.command("financial-followup")
def financial_followup(
    title: str,
    description: str | None = typer.Option(None, help="Optional task description"),
    due_at: str | None = typer.Option(None, help="ISO 8601 due datetime"),
):
    with session_scope() as session:
        due = datetime.fromisoformat(due_at) if due_at else None
        result = LifeAgent(session).ingest_financial_followup(title, description, due_at=due)
        typer.echo(json.dumps(to_plain(result), ensure_ascii=False, indent=2, default=str))
