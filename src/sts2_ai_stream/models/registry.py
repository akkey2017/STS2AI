from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from sts2_ai_stream.timeutil import utc_now


class ModelRegistry:
    def __init__(self, checkpoints_dir: Path):
        self.checkpoints_dir = checkpoints_dir
        self.registry_path = checkpoints_dir / "registry.json"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def summary(self) -> dict[str, Any]:
        return {
            "current_namespace": self._data.get("current_namespace"),
            "aliases": self._data.get("aliases", {}),
            "namespaces": self._data.get("namespaces", []),
        }

    def reset(self, reason: str, operator: str) -> dict[str, Any]:
        old_namespace = self._data.get("current_namespace")
        namespace = f"run_{utc_now().replace(':', '').replace('-', '')}_{uuid.uuid4().hex[:8]}"
        path = self.checkpoints_dir / namespace
        path.mkdir(parents=True, exist_ok=False)
        metadata = {
            "namespace": namespace,
            "created_at": utc_now(),
            "operator": operator,
            "reason": reason,
            "status": "empty",
        }
        (path / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        self._data["current_namespace"] = namespace
        self._data.setdefault("namespaces", []).append(metadata)
        self._save()
        return {
            "old_namespace": old_namespace,
            "new_namespace": namespace,
            "metadata": metadata,
        }

    def promote(self, alias: str, model_id: str, operator: str) -> dict[str, Any]:
        old_model_id = self._data.setdefault("aliases", {}).get(alias)
        self._data["aliases"][alias] = model_id
        self._save()
        return {
            "alias": alias,
            "old_model_id": old_model_id,
            "new_model_id": model_id,
            "operator": operator,
            "promoted_at": utc_now(),
        }

    def _load(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"current_namespace": None, "aliases": {}, "namespaces": []}
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"current_namespace": None, "aliases": {}, "namespaces": []}

    def _save(self) -> None:
        self.registry_path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

