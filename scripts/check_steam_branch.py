#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sts2_ai_stream.steam import main


if __name__ == "__main__":
    if len(sys.argv) == 1:
        library = Path(os.getenv("STEAM_LIBRARY_PATH", ""))
        app_id = os.getenv("STS2_STEAM_APP_ID", "2868840")
        if not str(library):
            print("Usage: check_steam_branch.py /path/to/appmanifest_2868840.acf", file=sys.stderr)
            print("Or set STEAM_LIBRARY_PATH to the Steam library containing steamapps/.", file=sys.stderr)
            raise SystemExit(2)
        sys.argv.append(str(library / "steamapps" / f"appmanifest_{app_id}.acf"))
    raise SystemExit(main())

