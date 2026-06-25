from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sts2_ai_stream.timeutil import utc_now


class JsonlEventStore:
    def __init__(self, data_dir: Path, audit_log: Path):
        self.data_dir = data_dir
        self.events_path = data_dir / "events" / "events.jsonl"
        self.logs_dir = data_dir / "logs"
        self.runs_dir = data_dir / "runs"
        self.audit_log = audit_log
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, payload: dict[str, Any], source: str = "system") -> dict[str, Any]:
        event = {
            "timestamp": utc_now(),
            "type": event_type,
            "source": source,
            "payload": payload,
        }
        self._append_jsonl(self.events_path, event)
        return event

    def append_control_action(
        self,
        operator: str,
        action: str,
        target: str,
        result: str,
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "operator": operator,
            "action": action,
            "target": target,
            "result": result,
            "detail": detail or {},
        }
        event = self.append("control.action", payload, source="control")
        self._append_jsonl(self.audit_log, event)
        return event

    def write_service_log(self, service: str, message: str) -> None:
        path = self.logs_dir / f"{service}.log"
        line = f"{utc_now()} {message}\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def tail_log(self, service: str, lines: int = 80) -> list[str]:
        path = self.logs_dir / f"{service}.log"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            content = handle.readlines()
        return [line.rstrip("\n") for line in content[-lines:]]

    def recent_events(self, event_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.events_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event_type is None or event.get("type") == event_type:
                    events.append(event)
        return events[-limit:]

    def recent_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.recent_events("run.ended", limit=limit)

    @staticmethod
    def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(obj, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

