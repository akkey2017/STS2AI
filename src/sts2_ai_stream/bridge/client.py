from __future__ import annotations

import json
import urllib.request
from typing import Any


class BridgeClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def state(self) -> dict[str, Any]:
        return self._get("/state")

    def actions(self) -> dict[str, Any]:
        return self._get("/actions")

    def act(self, action: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(action).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/act",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get(self, path: str) -> dict[str, Any]:
        with urllib.request.urlopen(self.base_url + path, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

