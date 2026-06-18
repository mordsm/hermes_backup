from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import DecisionLogEntry


class DecisionLog:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.entries: list[DecisionLogEntry] = []

    def add(self, module: str, kind: str, summary: str, payload: dict | None = None) -> DecisionLogEntry:
        entry = DecisionLogEntry(timestamp=datetime.now(timezone.utc), module=module, kind=kind, summary=summary, payload=payload or {})
        self.entries.append(entry)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(entry), default=str, ensure_ascii=False) + "\n")
        return entry
