from __future__ import annotations

from typing import Any

from sts2_ai_stream.config import Settings
from sts2_ai_stream.control.processes import MockProcessManager
from sts2_ai_stream.models import ModelRegistry
from sts2_ai_stream.telemetry import JsonlEventStore


class ControlCore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.ensure_dirs()
        self.events = JsonlEventStore(settings.data_dir, settings.control_audit_log)
        self.processes = MockProcessManager(settings.data_dir / "state" / "services.json", self.events)
        self.models = ModelRegistry(settings.data_dir / "checkpoints")

    def status(self) -> dict[str, Any]:
        return {
            "steam": {
                "app_id": self.settings.steam_app_id,
                "branch": self.settings.steam_branch,
                "expected_build_id": self.settings.expected_build_id,
            },
            "control": {
                "host": self.settings.control_host,
                "port": self.settings.control_port,
                "public_base_url": self.settings.control_public_base_url,
            },
            "services": self.processes.list(),
            "models": self.models.summary(),
            "recent_events": self.events.recent_events(limit=10),
        }

    def service_action(self, service: str, action: str, operator: str = "operator") -> dict[str, Any]:
        if action == "start":
            result = self.processes.start(service, operator=operator)
        elif action == "stop":
            result = self.processes.stop(service, operator=operator)
        elif action == "restart":
            result = self.processes.restart(service, operator=operator)
        else:
            raise ValueError(f"unsupported service action: {action}")
        self.events.append_control_action(operator, action, service, "ok", result)
        return result

    def logs(self, service: str, lines: int = 80) -> dict[str, Any]:
        return {"service": service, "lines": self.events.tail_log(service, lines=lines)}

    def reset_model(self, reason: str, operator: str = "operator") -> dict[str, Any]:
        result = self.models.reset(reason=reason, operator=operator)
        self.events.append("model.reset", result, source="control")
        self.events.append_control_action(operator, "reset-model", "models", "ok", result)
        return result

    def promote_model(self, alias: str, model_id: str, operator: str = "operator") -> dict[str, Any]:
        result = self.models.promote(alias=alias, model_id=model_id, operator=operator)
        self.events.append("model.promoted", result, source="control")
        self.events.append_control_action(operator, "promote-model", alias, "ok", result)
        return result

    def discord_test(self, operator: str = "operator") -> dict[str, Any]:
        result = {
            "configured": bool(self.settings.discord_webhook_url),
            "message": "discord webhook configured" if self.settings.discord_webhook_url else "discord webhook is not configured",
        }
        self.events.write_service_log("discord", f"test requested by {operator}: {result['message']}")
        self.events.append_control_action(operator, "test", "discord", "ok", result)
        return result

    def recent_runs(self, limit: int = 20) -> dict[str, Any]:
        return {"runs": self.events.recent_runs(limit=limit)}

