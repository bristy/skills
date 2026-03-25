---
name: xiaosu-search
version: 1.0.0
description: >
  Web search via 小宿智能搜索 V2 API (XiaoSu Smart Search). Use when internet search, web lookup,
  real-time information retrieval, news search, or fact-checking is needed. Supports time-filtered
  search (Day/Week/Month), long-form content extraction, smart snippet extraction, site-specific
  search, and site blocking. Triggers on "search the web", "look up", "find online", "latest news
  about", "search for", or any task requiring current internet data. NOT for local file search,
  memory search, or social media platform-specific queries (use sm-data-query for those).
metadata:
  openclaw:
    requires:
      envs:
        - XIAOSU_AK
        - XIAOSU_ENDPOINT
---

# 小宿智能搜索 V2

Web search API for real-time internet information retrieval.

## Setup (Required)

Set these environment variables before using this skill:

```bash
export XIAOSU_AK="<your-access-key>"
export XIAOSU_ENDPOINT="<your-endpoint-path>"
```

Get your credentials at: https://www.xiaosuai.com (小宿智能搜索)

You can add them to your shell profile (`~/.bashrc` / `~/.zshrc`) or OpenClaw's `.env` file.

## Quick Usage

Run the search script directly:

```bash
python3 ~/.openclaw/skills/xiaosu-search/scripts/xiaosu_search.py "<query>" \
  --ak $XIAOSU_AK --endpoint $XIAOSU_ENDPOINT [options]
```

### Common Patterns

```bash
# Basic search
python3 scripts/xiaosu_search.py "宁德时代" --ak $AK --endpoint $EP

# Recent news (last 24h)
python3 scripts/xiaosu_search.py "CATL battery" --freshness Day --ak $AK --endpoint $EP

# With full content extraction (for deep reading)
python3 scripts/xiaosu_search.py "储能行业趋势" --content --content-type MARKDOWN --content-timeout 5 --ak $AK --endpoint $EP

# Smart snippets (relevant text fragments)
python3 scripts/xiaosu_search.py "固态电池进展" --main-text --ak $AK --endpoint $EP

# Site-specific search
python3 scripts/xiaosu_search.py "宁德时代" --sites finance.eastmoney.com --ak $AK --endpoint $EP

# Raw JSON output (for programmatic use)
python3 scripts/xiaosu_search.py "query" --json --ak $AK --endpoint $EP

# Pagination
python3 scripts/xiaosu_search.py "query" --count 20 --offset 20 --ak $AK --endpoint $EP
```

### Script Options

| Flag | Description |
|------|-------------|
| `--count N` | Results count: 10/20/30/40/50 |
| `--freshness X` | Time filter: Day, Week, Month |
| `--offset N` | Pagination offset |
| `--content` | Enable long-form content extraction |
| `--content-type T` | TEXT (default), MARKDOWN, HTML |
| `--content-timeout S` | Content read timeout (max 10s) |
| `--main-text` | Enable smart snippet extraction |
| `--sites HOST` | Restrict to site |
| `--block HOST` | Exclude site |
| `--no-cache` | Disable 10-min result cache |
| `--json` | Raw JSON output |

## Direct API Usage (curl)

```bash
curl -s -G "https://searchapi.xiaosuai.com/search/$XIAOSU_ENDPOINT/smart" \
  --data-urlencode "q=<query>" \
  --data-urlencode "count=10" \
  -H "Authorization: Bearer $XIAOSU_AK"
```

## Guidelines

- For news monitoring: use `--freshness Day` + `--count 20`
- For deep research: use `--content --content-type MARKDOWN --content-timeout 5`
- For fact-checking: use `--main-text` for relevant fragments without full content overhead
- Rate limit: 429 = QPS exceeded, back off and retry
- Results have a `score` field (0-1) indicating relevance; prioritize high-score results
- API reference details: see [references/api-docs.md](references/api-docs.md)
