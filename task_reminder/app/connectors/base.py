from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExternalItem:
    source: str
    source_object_id: str
    title: str
    description: str | None = None
    due_at: datetime | None = None
    deadline_at: datetime | None = None
    source_url: str | None = None
    raw: dict | None = None


class Connector:
    source_name: str

    def sync(self) -> list[ExternalItem]:
        raise NotImplementedError

    def mark_done(self, source_object_id: str) -> None:
        raise NotImplementedError

    def get_source_url(self, source_object_id: str) -> str | None:
        return None
