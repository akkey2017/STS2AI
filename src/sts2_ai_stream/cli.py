from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from sts2_ai_stream.config import Settings
from sts2_ai_stream.control import run_control_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sts2ctl")
    parser.add_argument("--base-url", default=os.getenv("CONTROL_PUBLIC_BASE_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--token", default=os.getenv("CONTROL_AUTH_TOKEN", "dev-token-change-me"))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("serve-control")
    sub.add_parser("status")

    for command in ("start", "stop", "restart", "logs"):
        child = sub.add_parser(command)
        child.add_argument("service")
        if command == "logs":
            child.add_argument("--lines", type=int, default=80)
            child.add_argument("--follow", action="store_true")

    reset = sub.add_parser("reset-model")
    reset.add_argument("--reason", required=True)

    promote = sub.add_parser("promote-model")
    promote.add_argument("alias")
    promote.add_argument("model_id")

    sub.add_parser("models")
    runs = sub.add_parser("runs")
    runs.add_argument("--limit", type=int, default=20)
    sub.add_parser("discord-test")

    args = parser.parse_args(argv)
    if args.command == "serve-control":
        run_control_server(Settings.from_env())
        return 0

    client = ApiClient(args.base_url, args.token)
    try:
        if args.command == "status":
            print_status(client.get("/api/status"))
        elif args.command in {"start", "stop", "restart"}:
            print_json(client.post(f"/api/{args.service}/{args.command}", {}))
        elif args.command == "logs":
            show_logs(client, args.service, args.lines, args.follow)
        elif args.command == "reset-model":
            print_json(client.post("/api/models/reset", {"reason": args.reason}))
        elif args.command == "promote-model":
            print_json(client.post("/api/models/promote", {"alias": args.alias, "model_id": args.model_id}))
        elif args.command == "models":
            print_json(client.get("/api/models"))
        elif args.command == "runs":
            print_json(client.get(f"/api/runs?limit={args.limit}"))
        elif args.command == "discord-test":
            print_json(client.post("/api/discord/test", {}))
        else:
            parser.error(f"unknown command: {args.command}")
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8"), file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Control API is unreachable: {exc}", file=sys.stderr)
        return 1
    return 0


class ApiClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def get(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(self.base_url + path, headers=self._headers())
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={**self._headers(), "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def print_status(status: dict[str, Any]) -> None:
    steam = status["steam"]
    print(f"Steam: app={steam['app_id']} branch={steam['branch']} expected_build={steam['expected_build_id'] or 'not pinned'}")
    print("Services:")
    for service in status["services"]:
        print(f"  {service['name']:<10} {service['state']:<8} {service.get('message', '')}")
    models = status["models"]
    print(f"Model namespace: {models.get('current_namespace') or 'none'}")
    aliases = models.get("aliases") or {}
    if aliases:
        print("Aliases:")
        for alias, model_id in aliases.items():
            print(f"  {alias}: {model_id}")


def show_logs(client: ApiClient, service: str, lines: int, follow: bool) -> None:
    seen: list[str] = []
    while True:
        payload = client.get(f"/api/logs/{service}?lines={lines}")
        current = payload.get("lines", [])
        new_lines = current if not seen else current[len(seen) :]
        for line in new_lines:
            print(line)
        seen = current
        if not follow:
            break
        time.sleep(2)


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())

