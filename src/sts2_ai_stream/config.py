from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    steam_app_id: str
    steam_branch: str
    expected_build_id: str
    bridge_base_url: str
    bridge_base_port: int
    env_count: int
    display_base: str
    control_host: str
    control_port: int
    control_public_base_url: str
    control_auth_token: str
    control_audit_log: Path
    youtube_rtmp_url: str
    youtube_stream_key: str
    youtube_live_url: str
    discord_webhook_url: str

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "Settings":
        root = project_root or Path(os.getenv("STS2_PROJECT_ROOT", Path.cwd())).resolve()
        data_dir = root / os.getenv("STS2_DATA_DIR", "data")
        audit_log = root / os.getenv("CONTROL_AUDIT_LOG", "data/audit/control.jsonl")
        public_base_url = os.getenv("CONTROL_PUBLIC_BASE_URL")
        host = os.getenv("CONTROL_HOST", "0.0.0.0")
        port = _int_env("CONTROL_PORT", 8080)
        if not public_base_url:
            public_base_url = f"http://127.0.0.1:{port}"
        return cls(
            project_root=root,
            data_dir=data_dir,
            steam_app_id=os.getenv("STS2_STEAM_APP_ID", "2868840"),
            steam_branch=os.getenv("STS2_STEAM_BRANCH", "public-beta"),
            expected_build_id=os.getenv("STS2_EXPECTED_BUILD_ID", ""),
            bridge_base_url=os.getenv("STS2_BRIDGE_BASE_URL", "http://127.0.0.1:15526"),
            bridge_base_port=_int_env("STS2_BRIDGE_BASE_PORT", 15526),
            env_count=_int_env("STS2_ENV_COUNT", 10),
            display_base=os.getenv("STS2_DISPLAY_BASE", ":100"),
            control_host=host,
            control_port=port,
            control_public_base_url=public_base_url,
            control_auth_token=os.getenv("CONTROL_AUTH_TOKEN", "dev-token-change-me"),
            control_audit_log=audit_log,
            youtube_rtmp_url=os.getenv("YOUTUBE_RTMP_URL", ""),
            youtube_stream_key=os.getenv("YOUTUBE_STREAM_KEY", ""),
            youtube_live_url=os.getenv("YOUTUBE_LIVE_URL", ""),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL", ""),
        )

    def ensure_dirs(self) -> None:
        for path in (
            self.data_dir,
            self.data_dir / "logs",
            self.data_dir / "events",
            self.data_dir / "state",
            self.data_dir / "checkpoints",
            self.data_dir / "runs",
            self.data_dir / "audit",
            self.control_audit_log.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)

