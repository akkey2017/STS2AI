from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import parse_qs, urlparse

from sts2_ai_stream.config import Settings
from sts2_ai_stream.control.core import ControlCore


class ControlRequestHandler(BaseHTTPRequestHandler):
    core: ControlCore
    settings: Settings

    server_version = "STS2Control/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self._json({"ok": True})
            return
        if not self._authenticated(parsed.query):
            if parsed.path.startswith("/api/"):
                self._json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
                return
            self._login_page()
            return
        if parsed.query and "token=" in parsed.query:
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", f"sts2_token={self.settings.control_auth_token}; HttpOnly; SameSite=Lax")
            self.end_headers()
            return
        if parsed.path == "/":
            self._dashboard()
            return
        if parsed.path == "/api/status":
            self._json(self.core.status())
            return
        if parsed.path == "/api/models":
            self._json(self.core.models.summary())
            return
        if parsed.path == "/api/runs":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["20"])[0])
            self._json(self.core.recent_runs(limit=limit))
            return
        if parsed.path.startswith("/api/logs/"):
            service = parsed.path.rsplit("/", 1)[-1]
            query = parse_qs(parsed.query)
            lines = int(query.get("lines", ["80"])[0])
            self._json(self.core.logs(service, lines=lines))
            return
        self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/login":
            body = self._read_form()
            token = body.get("token", [""])[0]
            if token == self.settings.control_auth_token:
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", f"sts2_token={token}; HttpOnly; SameSite=Lax")
                self.end_headers()
            else:
                self._login_page(error="invalid token")
            return
        if not self._authenticated(parsed.query):
            self._json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
            return
        if parsed.path.startswith("/api/"):
            self._handle_api_post(parsed.path)
            return
        if parsed.path.startswith("/control/"):
            self._handle_form_post(parsed.path)
            return
        self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        self.core.events.write_service_log("control", fmt % args)

    def _handle_api_post(self, path: str) -> None:
        payload = self._read_json_or_form()
        operator = str(payload.get("operator") or "web")
        try:
            if path == "/api/models/reset":
                reason = str(payload.get("reason") or "manual reset")
                self._json(self.core.reset_model(reason=reason, operator=operator))
                return
            if path == "/api/models/promote":
                alias = str(payload.get("alias") or "")
                model_id = str(payload.get("model_id") or "")
                if not alias or not model_id:
                    self._json({"error": "alias and model_id are required"}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._json(self.core.promote_model(alias=alias, model_id=model_id, operator=operator))
                return
            if path == "/api/discord/test":
                self._json(self.core.discord_test(operator=operator))
                return
            parts = path.strip("/").split("/")
            if len(parts) == 3:
                _, service, action = parts
                self._json(self.core.service_action(service, action, operator=operator))
                return
        except ValueError as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_form_post(self, path: str) -> None:
        form = self._read_form()
        operator = form.get("operator", ["web"])[0]
        parts = path.strip("/").split("/")
        try:
            if parts == ["control", "models", "reset"]:
                reason = form.get("reason", ["manual reset"])[0]
                self.core.reset_model(reason=reason, operator=operator)
            elif parts == ["control", "discord", "test"]:
                self.core.discord_test(operator=operator)
            elif len(parts) == 3 and parts[0] == "control":
                _, service, action = parts
                self.core.service_action(service, action, operator=operator)
            else:
                self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
        except ValueError as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/")
        self.end_headers()

    def _authenticated(self, query: str = "") -> bool:
        token = self.settings.control_auth_token
        auth = self.headers.get("Authorization", "")
        if auth == f"Bearer {token}":
            return True
        if parse_qs(query).get("token", [""])[0] == token:
            return True
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            cookie = SimpleCookie(cookie_header)
            morsel = cookie.get("sts2_token")
            if morsel and morsel.value == token:
                return True
        return False

    def _read_form(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        return parse_qs(raw)

    def _read_json_or_form(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        if not raw:
            return {}
        if "application/json" in self.headers.get("Content-Type", ""):
            return json.loads(raw)
        return {key: values[0] if len(values) == 1 else values for key, values in parse_qs(raw).items()}

    def _json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str, status: HTTPStatus = HTTPStatus.OK, cookie: str | None = None) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _login_page(self, error: str = "") -> None:
        message = f"<p class='error'>{error}</p>" if error else ""
        self._html(
            f"""<!doctype html>
<html><head><meta charset="utf-8"><title>STS2 Control Login</title>{STYLE}</head>
<body><main class="login"><h1>STS2 Control</h1>{message}
<form method="post" action="/login">
<label>Control token <input name="token" type="password" autofocus></label>
<button type="submit">Login</button>
</form></main></body></html>""",
            status=HTTPStatus.UNAUTHORIZED,
        )

    def _dashboard(self) -> None:
        status = self.core.status()
        services = status["services"]
        service_rows = "\n".join(_service_row(service) for service in services)
        recent_events = "\n".join(
            f"<li><code>{event['timestamp']}</code> {event['type']} <small>{event['source']}</small></li>"
            for event in status["recent_events"]
        )
        model_summary = json.dumps(status["models"], ensure_ascii=False, indent=2)
        steam = status["steam"]
        self._html(
            f"""<!doctype html>
<html><head><meta charset="utf-8"><title>STS2 Control</title>{STYLE}</head>
<body>
<header><h1>STS2 Control</h1><p>Branch: <code>{steam['branch']}</code> Build: <code>{steam['expected_build_id'] or 'not pinned'}</code></p></header>
<main>
<section><h2>Services</h2><table><tr><th>Service</th><th>State</th><th>Message</th><th>Actions</th></tr>{service_rows}</table></section>
<section><h2>Models</h2><pre>{_escape(model_summary)}</pre>
<form method="post" action="/control/models/reset"><input name="reason" placeholder="reset reason" value="manual reset"><button>Reset model namespace</button></form></section>
<section><h2>Discord</h2><form method="post" action="/control/discord/test"><button>Test Discord webhook</button></form></section>
<section><h2>Recent Events</h2><ul>{recent_events}</ul></section>
<section><h2>API</h2><p><code>GET /api/status</code>, <code>GET /api/logs/training</code>, <code>POST /api/training/start</code></p></section>
</main></body></html>"""
        )


def _service_row(service: dict[str, Any]) -> str:
    name = str(service["name"])
    actions = " ".join(
        f'<form class="inline" method="post" action="/control/{name}/{action}"><button>{action}</button></form>'
        for action in ("start", "stop", "restart")
    )
    return (
        f"<tr><td><code>{name}</code></td><td>{service['state']}</td>"
        f"<td>{_escape(str(service.get('message', '')))}</td><td>{actions}</td></tr>"
    )


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


STYLE = """<style>
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:0;background:#101218;color:#eceff4}
header{padding:20px 28px;background:#171a23;border-bottom:1px solid #2f3443}
main{padding:24px;display:grid;gap:20px}
section{background:#171a23;border:1px solid #2f3443;border-radius:8px;padding:18px}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #2f3443;padding:8px;text-align:left}
button{background:#5e81ac;color:white;border:0;border-radius:6px;padding:7px 10px;cursor:pointer}
input{background:#101218;color:#eceff4;border:1px solid #4c566a;border-radius:6px;padding:8px}
code,pre{background:#0b0d12;border-radius:5px;padding:2px 4px}pre{padding:12px;overflow:auto}
.inline{display:inline;margin-right:6px}.login{max-width:420px;margin:15vh auto;background:#171a23;padding:28px;border-radius:8px}.error{color:#bf616a}
</style>"""


def run_control_server(settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    core = ControlCore(settings)
    handler = type(
        "ConfiguredControlRequestHandler",
        (ControlRequestHandler,),
        {"core": core, "settings": settings},
    )
    server = ThreadingHTTPServer((settings.control_host, settings.control_port), handler)
    core.events.write_service_log(
        "control",
        f"listening on {settings.control_host}:{settings.control_port}",
    )
    print(f"STS2 Control listening on http://{settings.control_host}:{settings.control_port}")
    print("Use CONTROL_AUTH_TOKEN to log in.")
    server.serve_forever()
