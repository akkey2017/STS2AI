#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

: "${DISPLAY:=${STS2_DISPLAY_BASE:-:100}}"
: "${BROADCAST_SIZE:=1920x1080}"
: "${BROADCAST_FPS:=30}"
: "${BROADCAST_ENCODER:=h264_nvenc}"
: "${BROADCAST_BITRATE:=8000k}"
export DISPLAY BROADCAST_SIZE BROADCAST_FPS BROADCAST_ENCODER BROADCAST_BITRATE

if [[ -z "${YOUTUBE_RTMP_URL:-}" || -z "${YOUTUBE_STREAM_KEY:-}" ]]; then
  echo "YOUTUBE_RTMP_URL and YOUTUBE_STREAM_KEY are required." >&2
  exit 2
fi

python3 - <<'PY'
import os
import shlex
from sts2_ai_stream.broadcast import build_ffmpeg_command

cmd = build_ffmpeg_command(
    display=os.environ["DISPLAY"],
    size=os.environ["BROADCAST_SIZE"],
    fps=int(os.environ["BROADCAST_FPS"]),
    rtmp_url=os.environ["YOUTUBE_RTMP_URL"],
    stream_key=os.environ["YOUTUBE_STREAM_KEY"],
    encoder=os.environ["BROADCAST_ENCODER"],
    bitrate=os.environ["BROADCAST_BITRATE"],
)
print(" ".join(shlex.quote(part) for part in cmd))
if os.environ.get("DRY_RUN") == "1":
    raise SystemExit(0)
os.execvp(cmd[0], cmd)
PY
