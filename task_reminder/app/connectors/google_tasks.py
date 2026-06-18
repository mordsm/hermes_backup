from .base import Connector, ExternalItem


class GoogleTasksConnector(Connector):
    source_name = "google_tasks"

    def sync(self) -> list[ExternalItem]:
        # TODO: implement Google Tasks sync.
        return []

    def mark_done(self, source_object_id: str) -> None:
        # TODO: mark Google Task completed.
        return None
