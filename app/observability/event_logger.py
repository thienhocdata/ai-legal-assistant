from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import json
from typing import Any


class JsonlEventLogger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = Lock()

    def log(self, event_type: str, payload: dict[str, Any]) -> None:
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **payload,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(row, ensure_ascii=False, default=str)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
