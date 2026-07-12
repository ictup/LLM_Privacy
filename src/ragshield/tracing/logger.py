"""Audit-friendly JSONL tracing."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    _path_locks: dict[Path, threading.Lock] = {}
    _path_locks_guard = threading.Lock()

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path = self.path.resolve()
        with self._path_locks_guard:
            self._lock = self._path_locks.setdefault(resolved_path, threading.Lock())

    def log(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **payload,
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        return event
