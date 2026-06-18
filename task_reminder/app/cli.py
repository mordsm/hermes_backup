import typer

from .db import session_scope, try_advisory_lock, release_advisory_lock
from .services.sync_service import SyncService
from .services.recurrence_service import RecurrenceService
from .services.alert_service import AlertService
from .services.completion_service import CompletionService
from .financial_agent.cli import financial_app
from .life_agent.cli import life_app

app = typer.Typer(help="Personal task reminder CLI")


@app.command()
def run_once():
    """Main command for Windows Task Scheduler."""
    with session_scope() as session:
        if not try_advisory_lock(session):
            typer.echo("Another run is already active. Exiting.")
            return

        try:
            SyncService(session).sync_all()
            RecurrenceService(session).generate_instances()
            AlertService(session).send_due_alerts()
        finally:
            release_advisory_lock(session)


@app.command()
def sync():
    with session_scope() as session:
        SyncService(session).sync_all()


@app.command("generate-instances")
def generate_instances():
    with session_scope() as session:
        RecurrenceService(session).generate_instances()


@app.command()
def alert():
    with session_scope() as session:
        AlertService(session).send_due_alerts()


@app.command("mark-done")
def mark_done(instance_id: str):
    with session_scope() as session:
        CompletionService(session).mark_done(instance_id)


@app.command()
def snooze(instance_id: str, minutes: int = 60):
    with session_scope() as session:
        CompletionService(session).snooze(instance_id, minutes)


@app.command()
def skip(instance_id: str):
    with session_scope() as session:
        CompletionService(session).skip(instance_id)


app.add_typer(financial_app, name="financial")
app.add_typer(life_app, name="life")

if __name__ == "__main__":
    app()
