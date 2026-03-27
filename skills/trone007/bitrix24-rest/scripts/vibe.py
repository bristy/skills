#!/usr/bin/env python3
"""Unified Vibe Platform CLI for Bitrix24 REST API.

Modes:
    Entity CRUD:  vibe.py deals --json
                  vibe.py deals/123 --json
                  vibe.py deals --create --body '{"title":"X"}' --confirm-write --json
                  vibe.py deals --update --id 123 --body '{"stageId":"WON"}' --confirm-write --json
                  vibe.py deals --delete --id 123 --confirm-destructive --json
                  vibe.py deals/search --body '{"filter":{...}}' --json
                  vibe.py deals/aggregate --body '{"field":"opportunity","function":"sum"}' --json
                  vibe.py deals/fields --json

    Raw:          vibe.py --raw GET /v1/chats/recent --json
                  vibe.py --raw POST /v1/notifications --body '{"..."}' --json

    Batch:        echo '[{"method":"GET","path":"/v1/deals"}]' | vibe.py --batch --json

    Iterate:      vibe.py deals --iterate --json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib import error, parse, request

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from vibe_config import load_key, cache_user_data, BASE_URL  # noqa: E402

MAX_PAGES = 200
RETRY_CODES = {429, 502}
MAX_RETRIES_429 = 3
MAX_RETRIES_502 = 2
DEFAULT_RETRY_AFTER = 45


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vibe Platform CLI for Bitrix24.")
    parser.add_argument("path", nargs="?", help="Entity path, e.g. 'deals', 'deals/123', 'deals/search'")
    parser.add_argument("--raw", nargs=2, metavar=("METHOD", "PATH"), help="Raw endpoint: --raw GET /v1/chats/recent")
    parser.add_argument("--batch", action="store_true", help="Batch mode: read JSON array from stdin")
    parser.add_argument("--create", action="store_true", help="Create entity")
    parser.add_argument("--update", action="store_true", help="Update entity")
    parser.add_argument("--delete", action="store_true", help="Delete entity")
    parser.add_argument("--id", help="Entity ID for update/delete")
    parser.add_argument("--body", help="JSON body for create/update/raw/search")
    parser.add_argument("--iterate", action="store_true", help="Auto-paginate, collect all pages")
    parser.add_argument("--max-items", type=int, help="Limit items when iterating")
    parser.add_argument("--page-size", type=int, default=50, help="Page size (default 50)")
    parser.add_argument("--confirm-write", action="store_true", help="Required for create/update")
    parser.add_argument("--confirm-destructive", action="store_true", help="Required for delete")
    parser.add_argument("--dry-run", action="store_true", help="Show request without executing")
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--config-file", help="Config file path override")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout seconds")
    return parser.parse_args()


def do_request(url: str, method: str, body: dict | None, api_key: str, timeout: float) -> dict:
    """Execute HTTP request with retry logic for 429 and 502."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body else None
    max_attempts = max(MAX_RETRIES_429, MAX_RETRIES_502) + 1

    for attempt in range(max_attempts):
        req = request.Request(url, data=data, headers=headers, method=method)
        resp_headers = {}
        try:
            with request.urlopen(req, timeout=timeout) as response:
                payload = response.read().decode("utf-8", errors="replace")
                status = response.getcode()
        except error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            status = exc.code
            resp_headers = dict(exc.headers) if exc.headers else {}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        # Retry logic
        if status == 429 and attempt < MAX_RETRIES_429:
            retry_after = int(resp_headers.get("Retry-After", DEFAULT_RETRY_AFTER))
            time.sleep(retry_after)
            continue
        if status == 502 and attempt < MAX_RETRIES_502:
            time.sleep(5)
            continue
        break

    try:
        parsed = json.loads(payload)
    except Exception:
        parsed = {"raw": payload}

    return {"ok": status < 400, "status": status, "data": parsed}


def resolve_entity_request(args: argparse.Namespace) -> tuple[str, str, dict | None]:
    """Resolve entity path + flags into (http_method, url_path, body)."""
    path = args.path
    body = json.loads(args.body) if args.body else None

    if args.delete:
        entity_id = args.id or (path.split("/")[1] if "/" in path else None)
        entity = path.split("/")[0]
        if not entity_id:
            raise ValueError("--delete requires --id or path like 'deals/123'")
        return "DELETE", f"/v1/{entity}/{entity_id}", None

    if args.update:
        entity_id = args.id or (path.split("/")[1] if "/" in path else None)
        entity = path.split("/")[0]
        if not entity_id:
            raise ValueError("--update requires --id or path like 'deals/123'")
        return "PUT", f"/v1/{entity}/{entity_id}", body

    if args.create:
        entity = path.split("/")[0] if path else ""
        return "POST", f"/v1/{entity}", body

    # Sub-resources: deals/search, deals/aggregate, deals/fields, deals/123
    if "/" in path:
        parts = path.split("/", 1)
        entity, sub = parts[0], parts[1]
        if sub in ("search", "aggregate"):
            return "POST", f"/v1/{entity}/{sub}", body
        elif sub == "fields":
            return "GET", f"/v1/{entity}/{sub}", None
        else:
            # deals/123 — get by ID
            return "GET", f"/v1/{entity}/{sub}", None

    # Default: list
    return "GET", f"/v1/{path}", None


def classify_operation(http_method: str, args: argparse.Namespace) -> str:
    """Classify as read/write/destructive."""
    if args.delete or http_method == "DELETE":
        return "destructive"
    if args.create or args.update or http_method in ("POST", "PUT", "PATCH"):
        # search and aggregate are POST but read-only
        if args.path and "/" in args.path:
            sub = args.path.split("/", 1)[1]
            if sub in ("search", "aggregate", "fields"):
                return "read"
        return "write"
    return "read"


def main() -> int:
    args = parse_args()
    api_key = load_key(args.config_file)

    if not api_key:
        result = {"ok": False, "error": "No Vibe API key configured. Run setup first."}
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.json else None))
        return 1

    # --- Batch mode ---
    if args.batch:
        stdin_data = sys.stdin.read()
        try:
            commands = json.loads(stdin_data)
        except json.JSONDecodeError as e:
            print(json.dumps({"ok": False, "error": f"Invalid JSON from stdin: {e}"}, indent=2))
            return 1
        if not isinstance(commands, list):
            print(json.dumps({"ok": False, "error": "Batch input must be a JSON array"}, indent=2))
            return 1

        results = {}
        for i, cmd in enumerate(commands):
            cmd_method = cmd.get("method", "GET")
            cmd_path = cmd.get("path", "")
            cmd_body = cmd.get("body")
            url = f"{BASE_URL}{cmd_path}"
            result = do_request(url, cmd_method, cmd_body, api_key, args.timeout)
            results[f"cmd{i}"] = result

        output = {"ok": all(r.get("ok") for r in results.values()), "results": results}
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.json else None))
        return 0 if output["ok"] else 1

    # --- Raw mode ---
    if args.raw:
        http_method, url_path = args.raw
        http_method = http_method.upper()
        body = json.loads(args.body) if args.body else None

        if args.dry_run:
            print(json.dumps({"dry_run": True, "method": http_method, "url": f"{BASE_URL}{url_path}"}, indent=2))
            return 0

        url = f"{BASE_URL}{url_path}"
        result = do_request(url, http_method, body, api_key, args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.json else None))
        return 0 if result.get("ok") else 1

    # --- Entity mode ---
    if not args.path:
        print(json.dumps({"ok": False, "error": "Provide entity path (e.g. 'deals') or use --raw/--batch"}, indent=2))
        return 1

    try:
        http_method, url_path, body = resolve_entity_request(args)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 1

    op_type = classify_operation(http_method, args)

    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "method": http_method,
            "url": f"{BASE_URL}{url_path}",
            "operation": op_type,
            "body": body,
        }, ensure_ascii=False, indent=2))
        return 0

    if op_type == "write" and not args.confirm_write:
        print(json.dumps({
            "ok": False,
            "error": f"Write operation requires --confirm-write flag",
            "operation": op_type,
        }, ensure_ascii=False, indent=2))
        return 2

    if op_type == "destructive" and not args.confirm_destructive:
        print(json.dumps({
            "ok": False,
            "error": f"Destructive operation requires --confirm-destructive flag",
            "operation": op_type,
        }, ensure_ascii=False, indent=2))
        return 2

    # --- Iterate mode ---
    if args.iterate:
        all_items = []
        page = 1
        total = None
        for _ in range(MAX_PAGES):
            sep = "&" if "?" in url_path else "?"
            paginated_path = f"{url_path}{sep}page={page}&pageSize={args.page_size}"
            url = f"{BASE_URL}{paginated_path}"
            result = do_request(url, http_method, body, api_key, args.timeout)

            if not result.get("ok"):
                print(json.dumps(result, ensure_ascii=False, indent=2 if args.json else None))
                return 1

            data = result.get("data", {})
            page_items = data.get("data", [])
            if not isinstance(page_items, list):
                page_items = []
            all_items.extend(page_items)

            if total is None:
                total = data.get("total", len(all_items))

            if args.max_items and len(all_items) >= args.max_items:
                all_items = all_items[:args.max_items]
                break

            if len(page_items) < args.page_size:
                break
            page += 1

        output = {"ok": True, "data": all_items, "total": total, "fetched": len(all_items)}
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.json else None))
        return 0

    # --- Single request ---
    url = f"{BASE_URL}{url_path}"
    result = do_request(url, http_method, body, api_key, args.timeout)

    # Auto-cache user data after /v1/me
    if url_path == "/v1/me" and result.get("ok"):
        user_data = result.get("data", {}).get("data", {})
        uid = user_data.get("id") or user_data.get("userId")
        tz = user_data.get("timezone", "")
        if uid:
            try:
                cache_user_data(int(uid), tz, args.config_file)
            except Exception:
                pass

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.json else None))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
