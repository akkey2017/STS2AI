from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from sts2_ai_stream.telemetry import JsonlEventStore
from sts2_ai_stream.timeutil import utc_now

ServiceState = Literal["stopped", "running", "error"]

DEFAULT_SERVICES = ("training", "env_pool", "spectator", "broadcast", "discord", "bridge")


@dataclass
class ServiceStatus:
    name: str
    state: ServiceState = "stopped"
    pid: int | None = None
    started_at: str | None = None
    stopped_at: str | None = None
    restart_count: int = 0
    message: str = "not started"


class MockProcessManager:
    def __init__(self, state_path: Path, event_store: JsonlEventStore):
        self.state_path = state_path
        self.event_store = event_store
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._services = self._load()

    def list(self) -> list[dict[str, object]]:
        return [asdict(self._services[name]) for name in sorted(self._services)]

    def get(self, name: str) -> dict[str, object]:
        self._ensure_service(name)
        return asdict(self._services[name])

    def start(self, name: str, operator: str = "system") -> dict[str, object]:
        self._ensure_service(name)
        status = self._services[name]
        if status.state == "running":
            status.message = "already running"
            self._save()
            return asdict(status)
        status.state = "running"
        status.pid = None
        status.started_at = utc_now()
        status.stopped_at = None
        status.message = "mock service running"
        self._save()
        self.event_store.write_service_log(name, f"started by {operator}")
        self.event_store.append("service.started", {"service": name, "operator": operator}, source="control")
        return asdict(status)

    def stop(self, name: str, operator: str = "system") -> dict[str, object]:
        self._ensure_service(name)
        status = self._services[name]
        if status.state == "stopped":
            status.message = "already stopped"
            self._save()
            return asdict(status)
        status.state = "stopped"
        status.pid = None
        status.stopped_at = utc_now()
        status.message = "mock service stopped"
        self._save()
        self.event_store.write_service_log(name, f"stopped by {operator}")
        self.event_store.append("service.stopped", {"service": name, "operator": operator}, source="control")
        return asdict(status)

    def restart(self, name: str, operator: str = "system") -> dict[str, object]:
        self._ensure_service(name)
        self.stop(name, operator=operator)
        status = self._services[name]
        status.restart_count += 1
        self.start(name, operator=operator)
        status = self._services[name]
        status.message = "mock service restarted"
        self._save()
        self.event_store.write_service_log(name, f"restarted by {operator}")
        self.event_store.append("service.restarted", {"service": name, "operator": operator}, source="control")
        return asdict(status)

    def _ensure_service(self, name: str) -> None:
        if name not in self._services:
            self._services[name] = ServiceStatus(name=name)

    def _load(self) -> dict[str, ServiceStatus]:
        services = {name: ServiceStatus(name=name) for name in DEFAULT_SERVICES}
        if not self.state_path.exists():
            return services
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return services
        for name, values in raw.items():
            try:
                services[name] = ServiceStatus(**values)
            except TypeError:
                continue
        return services

    def _save(self) -> None:
        raw = {name: asdict(status) for name, status in self._services.items()}
        self.state_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
