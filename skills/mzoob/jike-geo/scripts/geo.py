#!/usr/bin/env python3
"""
极义GEO CLI — OpenClaw skill script for GEO platform API.

Usage:
  python3 geo.py check
  python3 geo.py quota
  python3 geo.py products list|create|get|update|delete
  python3 geo.py company get|save
  python3 geo.py keywords list|add|delete
  python3 geo.py questions generate|list|toggle
  python3 geo.py search create|batch|status|batch-status|history
  python3 geo.py articles generate|list|get|update|delete
  python3 geo.py publish record|list
  python3 geo.py platforms list
  python3 geo.py ai-platforms

Configuration:
  Edit scripts/config.json to set secret_key and base_url.
  Environment variables JIKE_GEO_SECRET_KEY / JIKE_GEO_BASE_URL override config.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

DEFAULT_BASE_URL = "https://api.jike-geo.100.city"
POLL_INTERVAL = 3
MAX_POLL_SECONDS = 300

_config_cache = None


def load_config() -> dict:
    """Load config from config.json, cache it."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not os.path.exists(CONFIG_PATH):
        _config_cache = {}
        return _config_cache

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to read config.json: {e}", file=sys.stderr)
        _config_cache = {}
    return _config_cache


def get_config():
    """Resolve secret_key and base_url. Environment variable overrides config.json for key."""
    cfg = load_config()

    # secret_key: env > config.json
    key = os.environ.get("JIKE_GEO_SECRET_KEY", "").strip()
    if not key:
        key = (cfg.get("secret_key") or "").strip()
    if not key:
        print("Error: secret_key not configured.", file=sys.stderr)
        print(f"  Set it in {CONFIG_PATH} or via JIKE_GEO_SECRET_KEY env var.", file=sys.stderr)
        print("  Get your API Key at: https://jike-geo.100.city", file=sys.stderr)
        sys.exit(1)

    base = DEFAULT_BASE_URL

    return key, base


def get_default_product_id() -> str | None:
    """Get default product_id from config.json."""
    cfg = load_config()
    pid = cfg.get("product_id")
    return str(pid) if pid else None


def get_poll_settings() -> tuple[int, int]:
    """Get poll_interval and poll_timeout from config.json."""
    cfg = load_config()
    interval = cfg.get("poll_interval", POLL_INTERVAL)
    timeout = cfg.get("poll_timeout", MAX_POLL_SECONDS)
    return int(interval), int(timeout)

def api_request(method: str, path: str, body=None, product_id=None,
                 query: dict | None = None, raw: bool = False) -> dict:
    """Send HTTP request to GEO API. Returns parsed JSON response."""
    key, base = get_config()
    url = f"{base}{path}"
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})

    headers = {
        "X-API-Key": key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if product_id:
        headers["X-Product-ID"] = str(product_id)

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("message", err_body)
        except Exception:
            msg = err_body
        print(f"Error: HTTP {e.code} — {msg}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Connection failed — {e.reason}", file=sys.stderr)
        sys.exit(1)

    if raw:
        return result
    if isinstance(result, dict) and result.get("code", 0) != 0:
        print(f"Error: {result.get('message', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)
    return result.get("data") if isinstance(result, dict) else result


def fmt_json(data, use_json: bool = False):
    """Print data as JSON or return for formatting."""
    if use_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return True
    return False


def resolve_product_id(args) -> str:
    """Resolve product_id from args or config.json default."""
    pid = getattr(args, "product_id", None)
    if not pid:
        pid = get_default_product_id()
    if not pid:
        print("Error: --product-id required (or set product_id in config.json)", file=sys.stderr)
        sys.exit(1)
    return pid


# ---------------------------------------------------------------------------
# Commands: check / quota
# ---------------------------------------------------------------------------


def cmd_check(_args):
    key, base = get_config()
    print(f"Config:   {CONFIG_PATH}")
    print(f"Base URL: {base}")
    print(f"Key:      {key[:8]}...{key[-4:]}" if len(key) > 12 else f"Key: {key}")
    pid = get_default_product_id()
    if pid:
        print(f"Product:  {pid} (default)")
    try:
        data = api_request("GET", "/api/v1/user/info")
        print(f"Status:   OK")
        if data:
            print(f"Phone:    {data.get('phone', 'N/A')}")
            print(f"User ID:  {data.get('id', 'N/A')}")
    except SystemExit:
        print("Status:   FAILED — check your secret key")
        print("  Get your API Key at: https://jike-geo.100.city")
        sys.exit(1)


def cmd_quota(args):
    data = api_request("GET", "/api/v1/user/quota")
    if fmt_json(data, args.json):
        return
    print(f"套餐: {data.get('package_name', 'N/A')}")
    print(f"产品: {data.get('products_used', 0)}/{data.get('max_products', 0) or '∞'}")
    print(f"问题: {data.get('questions_used', 0)}/{data.get('max_questions', 0) or '∞'}")
    print(f"文章: {data.get('articles_used', 0)}/{data.get('max_articles', 0) or '∞'}")
    exp = data.get("expire_at", "")
    expired = data.get("expired", False)
    print(f"到期: {exp}" + (" ⚠️ 已过期" if expired else ""))


# ---------------------------------------------------------------------------
# Commands: products
# ---------------------------------------------------------------------------


def cmd_products(args):
    action = args.action
    if action == "list":
        data = api_request("GET", "/api/v1/products")
        if fmt_json(data, args.json):
            return
        if not data:
            print("暂无产品")
            return
        for p in data:
            print(f"[{p['id']}] {p['name']}  — {p.get('description', '')}")

    elif action == "create":
        if not args.name:
            print("Error: --name required", file=sys.stderr); sys.exit(1)
        body = {"name": args.name, "description": args.description or ""}
        data = api_request("POST", "/api/v1/products", body)
        if fmt_json(data, args.json):
            return
        print(f"产品创建成功: [{data['id']}] {data['name']}")

    elif action == "get":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        data = api_request("GET", f"/api/v1/products/{args.id}")
        if fmt_json(data, args.json):
            return
        print(json.dumps(data, ensure_ascii=False, indent=2))

    elif action == "update":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        body = {}
        if args.name: body["name"] = args.name
        if args.description: body["description"] = args.description
        data = api_request("PUT", f"/api/v1/products/{args.id}", body)
        print("产品更新成功")

    elif action == "delete":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        api_request("DELETE", f"/api/v1/products/{args.id}")
        print(f"产品 {args.id} 已删除")


# ---------------------------------------------------------------------------
# Commands: company
# ---------------------------------------------------------------------------


def cmd_company(args):
    pid = resolve_product_id(args)

    if args.action == "get":
        data = api_request("GET", "/api/v1/company", product_id=pid)
        if fmt_json(data, args.json):
            return
        if not data:
            print("该产品暂无公司信息")
            return
        for k in ["product_name", "company_name", "industry", "business_scope",
                   "cities", "contact_phone", "website", "description"]:
            print(f"{k}: {data.get(k, '')}")

    elif args.action == "save":
        body = {}
        for k in ["product_name", "company_name", "industry", "business_scope",
                   "cities", "contact_phone", "website", "description"]:
            v = getattr(args, k.replace("-", "_"), None)
            if v is not None:
                body[k] = v
        if not body:
            print("Error: at least one field required", file=sys.stderr); sys.exit(1)
        data = api_request("POST", "/api/v1/company", body, product_id=pid)
        if fmt_json(data, args.json):
            return
        print("公司信息保存成功")


# ---------------------------------------------------------------------------
# Commands: keywords
# ---------------------------------------------------------------------------


def cmd_keywords(args):
    pid = resolve_product_id(args)

    if args.action == "list":
        data = api_request("GET", "/api/v1/keywords", product_id=pid)
        if fmt_json(data, args.json):
            return
        if not data:
            print("暂无核心词")
            return
        for kw in data:
            print(f"[{kw['id']}] {kw['word']}")

    elif args.action == "add":
        if not args.word:
            print("Error: --word required", file=sys.stderr); sys.exit(1)
        data = api_request("POST", "/api/v1/keywords", {"word": args.word}, product_id=pid)
        if fmt_json(data, args.json):
            return
        print(f"核心词添加成功: [{data['id']}] {data['word']}")

    elif args.action == "delete":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        api_request("DELETE", f"/api/v1/keywords/{args.id}", product_id=pid)
        print(f"核心词 {args.id} 已删除")


# ---------------------------------------------------------------------------
# Commands: questions
# ---------------------------------------------------------------------------


def cmd_questions(args):
    pid = resolve_product_id(args)

    if args.action == "generate":
        if not args.keyword_ids:
            print("Error: --keyword-ids required (comma-separated)", file=sys.stderr); sys.exit(1)
        ids = [int(x.strip()) for x in args.keyword_ids.split(",")]
        data = api_request("POST", "/api/v1/questions/generate",
                           {"keyword_ids": ids}, product_id=pid)
        if fmt_json(data, args.json):
            return
        if isinstance(data, list):
            print(f"生成了 {len(data)} 个问题:")
            for q in data:
                print(f"  [{q['id']}] ({q.get('stage', '?')}) {q['content']}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.action == "list":
        query = {}
        if args.keyword_id:
            query["keyword_id"] = args.keyword_id
        data = api_request("GET", "/api/v1/questions", product_id=pid, query=query)
        if fmt_json(data, args.json):
            return
        stages = {"inquiry": "L1 认知", "understanding": "L2 探索",
                  "consideration": "L3 评估", "purchase": "L4 决策"}
        if isinstance(data, dict):
            for stage_key, label in stages.items():
                qs = data.get(stage_key, [])
                if qs:
                    print(f"\n{label}:")
                    for q in qs:
                        sel = "✓" if q.get("selected") else " "
                        print(f"  [{sel}] [{q['id']}] {q['content']}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.action == "toggle":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        api_request("PUT", f"/api/v1/questions/{args.id}/toggle", product_id=pid)
        print(f"问题 {args.id} 选中状态已切换")


# ---------------------------------------------------------------------------
# Commands: search (core GEO functionality)
# ---------------------------------------------------------------------------


def poll_task(task_id, product_id, is_batch=False):
    """Poll a search task until completion."""
    interval, timeout = get_poll_settings()
    endpoint = "batch" if is_batch else "task"
    elapsed = 0
    while elapsed < timeout:
        data = api_request("GET", f"/api/v1/geo-search/{endpoint}/{task_id}",
                           product_id=product_id)
        status = data.get("status", "unknown")
        if status in ("completed", "done", "finished"):
            return data
        if status in ("failed", "error"):
            print(f"Error: Task failed — {data.get('error', 'unknown')}", file=sys.stderr)
            sys.exit(1)
        # Show progress
        if is_batch:
            total = data.get("total_tasks", 0)
            done = data.get("completed_tasks", 0)
            print(f"  进度: {done}/{total} ({status})", end="\r")
        else:
            results = data.get("results", [])
            print(f"  已完成: {len(results)} 个平台 ({status})", end="\r")
        time.sleep(interval)
        elapsed += interval
    print("\nWarning: Polling timeout, use 'search status' to check later", file=sys.stderr)
    return data


def format_search_result(data, use_json=False):
    """Format GEO search results for display."""
    if use_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    question = data.get("question", "")
    brand = data.get("brand", "")
    status = data.get("status", "")
    print(f"问题: {question}")
    print(f"品牌: {brand}")
    print(f"状态: {status}")

    results = data.get("results", [])
    if not results:
        print("暂无结果")
        return

    mentioned = sum(1 for r in results if r.get("brand_mentioned"))
    print(f"品牌提及: {mentioned}/{len(results)} 个平台\n")

    for r in results:
        platform = r.get("platform", "unknown")
        bm = "✓ 提及" if r.get("brand_mentioned") else "✗ 未提及"
        rank = r.get("brand_rank", 0)
        sentiment = r.get("sentiment", "N/A")
        print(f"【{platform}】{bm}  排名: {rank or '-'}  情感: {sentiment}")

        citations = r.get("citations", [])
        if citations:
            print(f"  引用来源 ({len(citations)}):")
            for c in citations[:5]:
                print(f"    [{c.get('position', '?')}] {c.get('title', '')} — {c.get('domain', '')}")

        answer = r.get("answer", "")
        if answer:
            preview = answer[:150].replace("\n", " ")
            print(f"  回答: {preview}...")
        print()


def cmd_search(args):
    pid = resolve_product_id(args)

    if args.action == "create":
        if not args.question:
            print("Error: --question required", file=sys.stderr); sys.exit(1)
        body = {
            "question": args.question,
            "brand": args.brand or "",
            "mode": args.mode or "api",
        }
        if args.platforms:
            body["platforms"] = [p.strip() for p in args.platforms.split(",")]
        data = api_request("POST", "/api/v1/geo-search/task", body, product_id=pid)
        task_id = data.get("task_id", "")
        print(f"搜索任务已创建: {task_id}")

        if not args.no_wait:
            print("等待搜索完成...")
            result = poll_task(task_id, pid)
            print()
            format_search_result(result, args.json)
        else:
            print(f"使用 'search status --task-id {task_id}' 查看结果")

    elif args.action == "batch":
        if not args.question_ids:
            print("Error: --question-ids required (comma-separated)", file=sys.stderr); sys.exit(1)
        ids = [int(x.strip()) for x in args.question_ids.split(",")]
        body = {"question_ids": ids}
        if args.platforms:
            body["platforms"] = [p.strip() for p in args.platforms.split(",")]
        data = api_request("POST", "/api/v1/geo-search/batch", body, product_id=pid)
        batch_id = data.get("batch_id", "")
        print(f"批量任务已创建: {batch_id}")

        if not args.no_wait:
            print("等待批量搜索完成...")
            result = poll_task(batch_id, pid, is_batch=True)
            print()
            if fmt_json(result, args.json):
                return
            total = result.get("total_tasks", 0)
            done = result.get("completed_tasks", 0)
            print(f"批量任务完成: {done}/{total}")
            tasks = result.get("tasks", [])
            for t in tasks:
                bm = "✓" if any(r.get("brand_mentioned") for r in t.get("results", [])) else "✗"
                print(f"  [{t.get('task_id', '?')[:8]}] {bm} {t.get('question', '')}")
        else:
            print(f"使用 'search batch-status --batch-id {batch_id}' 查看进度")

    elif args.action == "status":
        if not args.task_id:
            print("Error: --task-id required", file=sys.stderr); sys.exit(1)
        data = api_request("GET", f"/api/v1/geo-search/task/{args.task_id}",
                           product_id=pid)
        format_search_result(data, args.json)

    elif args.action == "batch-status":
        if not args.batch_id:
            print("Error: --batch-id required", file=sys.stderr); sys.exit(1)
        data = api_request("GET", f"/api/v1/geo-search/batch/{args.batch_id}",
                           product_id=pid)
        if fmt_json(data, args.json):
            return
        total = data.get("total_tasks", 0)
        done = data.get("completed_tasks", 0)
        status = data.get("status", "unknown")
        print(f"批量任务: {status}  进度: {done}/{total}")
        tasks = data.get("tasks", [])
        for t in tasks:
            print(f"  [{t.get('task_id', '?')[:8]}] {t.get('status', '?')} — {t.get('question', '')}")

    elif args.action == "history":
        query = {}
        if args.page: query["page"] = args.page
        if args.size: query["size"] = args.size
        data = api_request("GET", "/api/v1/geo-search/history",
                           product_id=pid, query=query)
        if fmt_json(data, args.json):
            return
        records = data if isinstance(data, list) else data.get("list", [])
        if not records:
            print("暂无搜索历史")
            return
        for r in records:
            tid = r.get("task_id", "")[:8]
            q = r.get("question", "")
            s = r.get("status", "")
            print(f"  [{tid}] {s} — {q}")


# ---------------------------------------------------------------------------
# Commands: articles
# ---------------------------------------------------------------------------


def cmd_articles(args):
    pid = resolve_product_id(args)

    if args.action == "generate":
        if not args.question_id:
            print("Error: --question-id required", file=sys.stderr); sys.exit(1)
        body = {"question_id": int(args.question_id)}
        if args.instruction:
            body["instruction"] = args.instruction
        if args.image_ids:
            body["image_ids"] = [int(x.strip()) for x in args.image_ids.split(",")]
        data = api_request("POST", "/api/v1/articles/generate", body, product_id=pid)
        if fmt_json(data, args.json):
            return
        print(f"文章生成成功: [{data.get('id', '?')}] {data.get('title', '')}")
        content = data.get("content", "")
        if content:
            preview = content[:300].replace("\n", "\n  ")
            print(f"\n  {preview}...")

    elif args.action == "list":
        query = {}
        if args.question_id:
            query["question_id"] = args.question_id
        data = api_request("GET", "/api/v1/articles", product_id=pid, query=query)
        if fmt_json(data, args.json):
            return
        if not data:
            print("暂无文章")
            return
        for a in data:
            status = a.get("status", "draft")
            print(f"[{a['id']}] ({status}) {a.get('title', 'Untitled')}")

    elif args.action == "get":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        data = api_request("GET", f"/api/v1/articles/{args.id}", product_id=pid)
        if fmt_json(data, args.json):
            return
        article = data.get("article", data)
        print(f"标题: {article.get('title', '')}")
        print(f"状态: {article.get('status', '')}")
        print(f"\n{article.get('content', '')}")

    elif args.action == "update":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        body = {}
        if args.title: body["title"] = args.title
        if args.content: body["content"] = args.content
        if args.status: body["status"] = args.status
        api_request("PUT", f"/api/v1/articles/{args.id}", body, product_id=pid)
        print("文章更新成功")

    elif args.action == "delete":
        if not args.id:
            print("Error: --id required", file=sys.stderr); sys.exit(1)
        api_request("DELETE", f"/api/v1/articles/{args.id}", product_id=pid)
        print(f"文章 {args.id} 已删除")


# ---------------------------------------------------------------------------
# Commands: publish / platforms / ai-platforms
# ---------------------------------------------------------------------------


def cmd_publish(args):
    pid = resolve_product_id(args)

    if args.action == "record":
        if not args.article_id or not args.platform_id:
            print("Error: --article-id and --platform-id required", file=sys.stderr); sys.exit(1)
        body = {
            "article_id": int(args.article_id),
            "platform_id": int(args.platform_id),
        }
        if args.platform_name:
            body["platform"] = args.platform_name
        api_request("POST", "/api/v1/publish", body, product_id=pid)
        print("发布记录已保存")

    elif args.action == "list":
        query = {}
        if args.article_id:
            query["article_id"] = args.article_id
        data = api_request("GET", "/api/v1/publish/records", product_id=pid, query=query)
        if fmt_json(data, args.json):
            return
        if not data:
            print("暂无发布记录")
            return
        for r in data:
            print(f"[{r.get('id', '?')}] 文章{r.get('article_id', '?')} → {r.get('platform', '?')}")


def cmd_platforms(args):
    data = api_request("GET", "/api/v1/platforms")
    if fmt_json(data, args.json):
        return
    if not data:
        print("暂无平台")
        return
    for p in data:
        ptype = "预设" if p.get("type") == "preset" else "自定义"
        print(f"[{p['id']}] {p['name']} ({ptype}) — {p.get('url', '')}")


def cmd_ai_platforms(args):
    data = api_request("GET", "/api/v1/ai-platforms")
    if fmt_json(data, args.json):
        return
    if not data:
        print("暂无 AI 平台")
        return
    for p in data:
        color = p.get("color", "")
        print(f"[{p['id']}] {p['name']}  {color}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="geo.py",
        description="极义GEO CLI — AI 搜索引擎优化平台",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # check
    sub.add_parser("check", help="检查连接和认证")

    # quota
    p = sub.add_parser("quota", help="查询额度")
    p.add_argument("--json", action="store_true")

    # products
    p = sub.add_parser("products", help="产品管理")
    p.add_argument("action", choices=["list", "create", "get", "update", "delete"])
    p.add_argument("--id", type=int)
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--json", action="store_true")

    # company
    p = sub.add_parser("company", help="公司信息")
    p.add_argument("action", choices=["get", "save"])
    p.add_argument("--product-id", type=int)
    p.add_argument("--product-name")
    p.add_argument("--company-name")
    p.add_argument("--industry")
    p.add_argument("--business-scope")
    p.add_argument("--cities")
    p.add_argument("--contact-phone")
    p.add_argument("--website")
    p.add_argument("--description")
    p.add_argument("--json", action="store_true")

    # keywords
    p = sub.add_parser("keywords", help="核心词管理")
    p.add_argument("action", choices=["list", "add", "delete"])
    p.add_argument("--product-id", type=int)
    p.add_argument("--id", type=int)
    p.add_argument("--word")
    p.add_argument("--json", action="store_true")

    # questions
    p = sub.add_parser("questions", help="问题管理")
    p.add_argument("action", choices=["generate", "list", "toggle"])
    p.add_argument("--product-id", type=int)
    p.add_argument("--id", type=int)
    p.add_argument("--keyword-id", type=int)
    p.add_argument("--keyword-ids")
    p.add_argument("--json", action="store_true")

    # search
    p = sub.add_parser("search", help="GEO 搜索")
    p.add_argument("action", choices=["create", "batch", "status", "batch-status", "history"])
    p.add_argument("--product-id", type=int)
    p.add_argument("--question")
    p.add_argument("--brand")
    p.add_argument("--platforms")
    p.add_argument("--mode", default="api", choices=["api", "plugin"])
    p.add_argument("--task-id")
    p.add_argument("--batch-id")
    p.add_argument("--question-ids")
    p.add_argument("--no-wait", action="store_true", help="不等待结果")
    p.add_argument("--page", type=int)
    p.add_argument("--size", type=int)
    p.add_argument("--json", action="store_true")

    # articles
    p = sub.add_parser("articles", help="文章管理")
    p.add_argument("action", choices=["generate", "list", "get", "update", "delete"])
    p.add_argument("--product-id", type=int)
    p.add_argument("--id", type=int)
    p.add_argument("--question-id", type=int)
    p.add_argument("--instruction")
    p.add_argument("--image-ids")
    p.add_argument("--title")
    p.add_argument("--content")
    p.add_argument("--status", choices=["draft", "published"])
    p.add_argument("--json", action="store_true")

    # publish
    p = sub.add_parser("publish", help="发布记录")
    p.add_argument("action", choices=["record", "list"])
    p.add_argument("--product-id", type=int)
    p.add_argument("--article-id", type=int)
    p.add_argument("--platform-id", type=int)
    p.add_argument("--platform-name")
    p.add_argument("--json", action="store_true")

    # platforms
    p = sub.add_parser("platforms", help="自媒体平台列表")
    p.add_argument("--json", action="store_true")

    # ai-platforms
    p = sub.add_parser("ai-platforms", help="AI 搜索平台列表")
    p.add_argument("--json", action="store_true")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMAND_MAP = {
    "check": cmd_check,
    "quota": cmd_quota,
    "products": cmd_products,
    "company": cmd_company,
    "keywords": cmd_keywords,
    "questions": cmd_questions,
    "search": cmd_search,
    "articles": cmd_articles,
    "publish": cmd_publish,
    "platforms": cmd_platforms,
    "ai-platforms": cmd_ai_platforms,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_MAP.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
