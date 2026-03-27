---
name: searxng-search-cli
displayName: SearXNG Search CLI (Free, Self-hosted, Auto-deploy, Multi-Channel)
description: |
  Use self-hosted SearXNG search engine (Free, Self-hosted, Auto-deploy, Multi-Channel). SearXNG is a free meta search engine that aggregates 200+ search engines (Google, Bing, Brave, GitHub, etc.), completely free and self-hostable.
  Trigger: User needs to search queries, research information, find resources, etc.
---

# SearXNG-CLI (Free, Self-hosted, Search Engine Aggregator) | SearXNG CLI（免费、自托管、搜索引擎聚合器）

Use SearXNG self-hosted search API for fast, accurate searching.

使用 SearXNG 自托管搜索 API 进行快速、准确的搜索。

## Quick Start | 快速开始

```bash
# One-click install and start | 一键安装 + 启动
searxng-search install

# Use | 使用
searxng-search search "your query"
```

## Command List | 命令列表

| Command | Description | 说明 |
|---------|-------------|------|
| install | One-click install SearXNG | 一键安装 SearXNG |
| start | Start service | 启动服务 |
| stop | Stop service | 停止服务 |
| restart | Restart service | 重启服务 |
| status | Check service status | 查看服务状态 |
| search \<query\> | Search | 搜索 |
| enable | Enable auto-start | 开机自启 |
| disable | Disable auto-start | 取消开机自启 |

## Installation | 安装 (install)

Automatically completes: | 自动完成以下步骤：
1. Install uv (if not installed) | 安装 uv (如未安装)
2. Clone SearXNG to ~/projects/searxng | 克隆 SearXNG 到 ~/projects/searxng
3. Create Python virtual environment | 创建 Python 虚拟环境
4. Install dependencies | 安装依赖
5. Enable JSON API | 启用 JSON API
6. Start service | 启动服务

```bash
searxng-search install
```

### Configuration | 配置

After installation, configure: | 安装后可配置以下环境变量：
- `SEARXNG_PORT` - Port (default 8888) | 端口 (默认 8888)
- `SEARXNG_HOST` - Bind address (default 127.0.0.1) | 绑定地址 (默认 127.0.0.1)
- `SEARXNG_SECRET` - Auth key (auto-generated) | 认证密钥 (自动生成)

## Service Management | 服务管理

```bash
# Start | 启动
searxng-search start

# Stop | 停止
searxng-search stop

# Restart | 重启
searxng-search restart

# Status | 状态
searxng-search status

# Enable auto-start | 开机自启
searxng-search enable

# Disable auto-start | 取消自启
searxng-search disable
```

## Search | 搜索

### Command Line | 命令行

```bash
searxng-search search "Python Tutorial"

# Specify engine | 指定引擎
searxng-search search "git clone" --engine github

# Specify language | 指定语言
searxng-search search "AI News" --lang zh

# Pagination | 分页
searxng-search search "llm" --page 2

# Time filter | 时间过滤
searxng-search search "python" --time-range month
```

### API Call | API 调用

```bash
# Basic search | 基本搜索
curl "http://127.0.0.1:8888/search?q=test&format=json"

# Specify engine and language | 指定引擎和语言
curl "http://127.0.0.1:8888/search?q=python&format=json&engines=github&lang=en"

# Time filter | 时间过滤
curl "http://127.0.0.1:8888/search?q=llm&format=json&time_range=month"
```

## Parameter Reference | 参数说明

### search parameters | search 参数

| Parameter | Short | Description | Example |
|-----------|-------|-------------|---------|
| --engine | -e | Specify engine | github, google |
| --lang | -l | Language | zh, en, auto |
| --page | -p | Page number | 1, 2, 3 |
| --time-range | -t | Time range | day, week, month, year |
| --safe-search | -s | Safe search | 0, 1, 2 |

### Available Engines | 可用引擎

General: google, bing, brave, duckduckgo, yandex, startpage, qwant
Code/Dev: github, gitlab, stackoverflow, npm, pypi
Academic: arxiv, pubmed, wikipedia, google-scholar
Video/Image: youtube, vimeo, pexels, pixabay

通用搜索：google, bing, brave, duckduckgo, yandex, startpage, qwant
代码/开发：github, gitlab, stackoverflow, npm, pypi
学术：arxiv, pubmed, wikipedia, google-scholar
视频/图片：youtube, vimeo, pexels, pixabay

## Troubleshooting | 故障排除

| Problem | Cause | Solution |
|---------|-------|----------|
| connection refused | Service not running | `searxng-search start` |
| 403 Forbidden | JSON not enabled | Re-run `install` |
| timeout | Engine blocked | Change engine or add proxy |
| Install failed | Permission issue | Check uv path |

## Project Structure | 项目结构

```
searxng-search/
├── SKILL.md
├── scripts/
│   └── searxng_cli.py      # CLI main program
└── references/
    └── settings.yml        # SearXNG config
```

## Related Documentation | 相关文档

- [SearXNG Official Docs](https://docs.searxng.org) | [SearXNG 官方文档](https://docs.searxng.org)
- [GitHub](https://github.com/searxng/searxng)
