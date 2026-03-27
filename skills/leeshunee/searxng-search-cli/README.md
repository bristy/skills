---
name: searxng-search
description: |
  使用自托管 SearXNG 搜索引擎进行搜索。SearXNG 是一个免费的元搜索引擎，
  聚合 200+ 搜索引擎（Google, Bing, Brave, GitHub 等），完全免费且可自托管。
  触发条件：用户需要搜索查询、调研信息、查找资源等。
---

# SearXNG Search - 搜索工具

使用 SearXNG 自托管搜索 API 进行快速、准确的搜索。

## 前置条件

### 安装 SearXNG

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# 2. 克隆 SearXNG
git clone --depth 1 https://github.com/searxng/searxng.git ~/projects/searxng

# 3. 创建虚拟环境
cd ~/projects/searxng
uv venv .venv
uv pip install -r requirements.txt

# 4. 启用 JSON API
sed -i 's/  formats:/  formats:\n    - json/' searx/settings.yml

# 5. 启动服务
SEARXNG_SECRET=mysecretkey .venv/bin/python -m searx.webapp --host 127.0.0.1 --port 8888 &
```

### 启动/停止

```bash
# 启动
cd ~/projects/searxng
SEARXNG_SECRET=mysecretkey .venv/bin/python -m searx.webapp --host 127.0.0.1 --port 8888 &

# 停止
pkill -f searx.webapp

# 检查状态
curl "http://127.0.0.1:8888/search?q=test&format=json"
```

## 使用方法

### API 调用

```bash
# 基本搜索
curl "http://127.0.0.1:8888/search?q=llm&format=json"

# 指定引擎和语言
curl "http://127.0.0.1:8888/search?q=python&format=json&engines=github&lang=en"

# 分页
curl "http://127.0.0.1:8888/search?q=AI&format=json&page=2"

# 时间过滤
curl "http://127.0.0.1:8888/search?q=llm&format=json&time_range=month"
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| q | 搜索关键词 | llm agent |
| format | 输出格式 | json |
| engines | 指定引擎 | google,brave,github |
| lang | 语言 | zh, en, auto |
| page | 页码 | 1, 2, 3 |
| time_range | 时间范围 | day, week, month, year |
| safesearch | 安全搜索 | 0, 1, 2 |

## 可用引擎

通用搜索：google, bing, brave, duckduckgo, yandex, startpage, qwant
代码/开发：github, gitlab, stackoverflow, npm, pypi
学术：arxiv, pubmed, wikipedia, google-scholar
视频/图片：youtube, vimeo, pexels, pixabay

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| connection refused | 服务未运行 | 启动 SearXNG |
| 403 Forbidden | JSON 未启用 | 编辑 settings.yml |
| timeout | 引擎被封 | 换引擎 |

## 相关文档

- SearXNG 官方文档: https://docs.searxng.org
- GitHub: https://github.com/searxng/searxng
