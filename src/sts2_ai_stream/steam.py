from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def inspect_appmanifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    text = path.read_text(encoding="utf-8", errors="replace")
    values = _extract_acf_values(text)
    return {
        "exists": True,
        "path": str(path),
        "appid": values.get("appid"),
        "name": values.get("name"),
        "buildid": values.get("buildid"),
        "betakey": values.get("betakey") or values.get("BetaKey") or values.get("beta"),
        "raw": values,
    }


def _extract_acf_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line in {"{", "}"}:
            continue
        parts = [part for part in line.split('"') if part and not part.isspace()]
        if len(parts) >= 2:
            key = parts[0].strip()
            value = parts[1].strip()
            values[key] = value
    return values


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--expected-branch", default="public-beta")
    parser.add_argument("--expected-build-id", default="")
    args = parser.parse_args()
    result = inspect_appmanifest(args.manifest)
    result["expected_branch"] = args.expected_branch
    result["expected_build_id"] = args.expected_build_id
    branch_ok = not args.expected_branch or result.get("betakey") in {args.expected_branch, None}
    build_ok = not args.expected_build_id or result.get("buildid") == args.expected_build_id
    result["ok"] = bool(result.get("exists")) and branch_ok and build_ok
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

