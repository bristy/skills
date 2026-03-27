#!/usr/bin/env python3
"""Check Vibe Platform connection using saved API key."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib import error, request

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from vibe_config import load_key, mask_key, BASE_URL, migrate_old_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Vibe Platform connection.")
    parser.add_argument("--config-file", help="Config file path override")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout seconds")
    return parser.parse_args()


def probe_me(api_key: str, timeout: float) -> dict:
    """Call GET /v1/me and return parsed result."""
    url = f"{BASE_URL}/v1/me"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8", errors="replace")
            status = response.getcode()
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    try:
        body = json.loads(payload)
    except Exception:
        body = {"raw": payload}

    return {"ok": status < 400, "status": status, "body": body}


def build_result(args: argparse.Namespace) -> dict:
    # Check for old config
    migrated = migrate_old_config(args.config_file)

    api_key = load_key(args.config_file)
    result = {
        "key_found": api_key is not None,
        "migrated_from_webhook": migrated,
    }

    if not api_key:
        result["connection_ok"] = False
        result["error"] = "No Vibe API key found in config"
        return result

    result["key_prefix"] = mask_key(api_key)

    probe = probe_me(api_key, args.timeout)
    if not probe.get("ok"):
        result["connection_ok"] = False
        result["error"] = probe.get("error") or f"HTTP {probe.get('status')}"
        return result

    result["connection_ok"] = True
    body = probe.get("body", {})
    data = body.get("data", body)
    result["scopes"] = data.get("scopes", [])
    result["portal"] = data.get("portal", "")
    result["user"] = data.get("name", data.get("user", ""))
    return result


def main() -> int:
    args = parse_args()
    result = build_result(args)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for k, v in result.items():
            print(f"{k}: {v}")

    return 0 if result.get("connection_ok") else 1


if __name__ == "__main__":
    sys.exit(main())
