#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sts2_ai_stream.bridge import BridgeClient


def main() -> int:
    base_url = os.getenv("STS2_BRIDGE_BASE_URL", "http://127.0.0.1:15526")
    client = BridgeClient(base_url)
    result = {
        "base_url": base_url,
        "state": client.state(),
        "actions": client.actions(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

