from __future__ import annotations

import json
import urllib.request


class DiscordReporter:
    def __init__(self, webhook_url: str, timeout: float = 10.0):
        self.webhook_url = webhook_url
        self.timeout = timeout

    def send_text(self, content: str) -> bool:
        if not self.webhook_url:
            return False
        payload = json.dumps({"content": content}).encode("utf-8")
        request = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return 200 <= response.status < 300

