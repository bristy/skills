#!/usr/bin/env python3
"""小宿智能搜索 V2 - Web Search Script

Usage:
  python3 xiaosu_search.py <query> [options]

Options:
  --count N          Number of results (10/20/30/40/50, default 10)
  --freshness DAY    Time filter: Day, Week, Month
  --offset N         Pagination offset (default 0)
  --content          Enable long-form content extraction
  --content-type T   Content format: TEXT, MARKDOWN, HTML (default TEXT)
  --content-timeout S  Content read timeout in seconds (max 10)
  --main-text        Enable smart snippet extraction
  --sites HOST       Restrict to specific site (host format)
  --block HOST       Block specific site (host format)
  --no-cache         Disable 10-min result cache
  --json             Output raw JSON
  --ak KEY           AccessKey (default: env XIAOSU_AK)
  --endpoint EP      Endpoint path (default: env XIAOSU_ENDPOINT)

Environment Variables:
  XIAOSU_AK          AccessKey for authentication
  XIAOSU_ENDPOINT    API endpoint path

Examples:
  python3 xiaosu_search.py "宁德时代固态电池"
  python3 xiaosu_search.py "CATL news" --freshness Day --count 20
  python3 xiaosu_search.py "储能行业" --content --content-type MARKDOWN
  python3 xiaosu_search.py "电池回收" --sites baidu.com --main-text
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

BASE_URL = "https://searchapi.xiaosuai.com/search"


def search(query, endpoint, ak, count=10, freshness=None, offset=0,
           enable_content=False, content_type="TEXT", content_timeout=None,
           main_text=False, sites=None, block_websites=None, no_cache=False):
    params = {"q": query}
    if count and count != 10:
        params["count"] = count
    if freshness:
        params["freshness"] = freshness
    if offset:
        params["offset"] = offset
    if enable_content:
        params["enableContent"] = "true"
        if content_type and content_type != "TEXT":
            params["contentType"] = content_type
        if content_timeout is not None:
            params["contentTimeout"] = content_timeout
    if main_text:
        params["mainText"] = "true"
    if sites:
        params["sites"] = sites
    if block_websites:
        params["blockWebsites"] = block_websites

    url = f"{BASE_URL}/{endpoint}/smart?{urllib.parse.urlencode(params)}"

    headers = {"Authorization": f"Bearer {ak}"}
    if no_cache:
        headers["Pragma"] = "no-cache"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def format_results(data):
    lines = []
    query = data.get("queryContext", {}).get("originalQuery", "")
    lines.append(f"Query: {query}")
    lines.append("")

    pages = data.get("webPages", {}).get("value", [])
    if not pages:
        lines.append("No results found.")
        return "\n".join(lines)

    for i, p in enumerate(pages, 1):
        title = p.get("name", "Untitled")
        url = p.get("url", "")
        snippet = p.get("snippet", "")
        date = p.get("datePublished", "")
        site = p.get("siteName", "")
        score = p.get("score", "")
        main_text = p.get("mainText", "")
        content = p.get("content", "")

        header = f"[{i}] {title}"
        if site:
            header += f" ({site})"
        if score:
            header += f" [score: {score}]"
        lines.append(header)
        lines.append(f"    URL: {url}")
        if date:
            lines.append(f"    Date: {date}")
        if snippet:
            lines.append(f"    Snippet: {snippet[:300]}")
        if main_text:
            lines.append(f"    MainText: {main_text[:300]}")
        if content:
            lines.append(f"    Content: {content[:500]}...")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="小宿智能搜索 V2")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--count", type=int, default=10, choices=[10, 20, 30, 40, 50])
    parser.add_argument("--freshness", choices=["Day", "Week", "Month"])
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--content", action="store_true", help="Enable long content")
    parser.add_argument("--content-type", default="TEXT", choices=["TEXT", "MARKDOWN", "HTML"])
    parser.add_argument("--content-timeout", type=float)
    parser.add_argument("--main-text", action="store_true", help="Enable smart snippets")
    parser.add_argument("--sites", help="Restrict to site (host format)")
    parser.add_argument("--block", help="Block site (host format)")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--ak", default=os.environ.get("XIAOSU_AK", ""))
    parser.add_argument("--endpoint", default=os.environ.get("XIAOSU_ENDPOINT", ""))

    args = parser.parse_args()

    if not args.ak:
        print("Error: --ak or XIAOSU_AK env required", file=sys.stderr)
        sys.exit(1)
    if not args.endpoint:
        print("Error: --endpoint or XIAOSU_ENDPOINT env required", file=sys.stderr)
        sys.exit(1)

    data = search(
        query=args.query,
        endpoint=args.endpoint,
        ak=args.ak,
        count=args.count,
        freshness=args.freshness,
        offset=args.offset,
        enable_content=args.content,
        content_type=args.content_type,
        content_timeout=args.content_timeout,
        main_text=args.main_text,
        sites=args.sites,
        block_websites=args.block,
        no_cache=args.no_cache,
    )

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_results(data))


if __name__ == "__main__":
    main()
