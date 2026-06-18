from .base import Connector, ExternalItem


class TrelloConnector(Connector):
    source_name = "trello"

    def sync(self) -> list[ExternalItem]:
        # TODO: implement Trello board/card sync.
        return []

    def mark_done(self, source_object_id: str) -> None:
        # TODO: set dueComplete=true or move card to Done list.
        return None
