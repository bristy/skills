# Changelog

## v2.1.0 (2026-03-20)

### English

**Highlights:**

- **New: `memory_search` Tool** — Agent can now proactively call the `memory_search` tool to search the memory database on demand, without relying on `before_prompt_build` hook. No extra latency on normal conversations.
- **New: Auto Session Archive via Cron** — Every 5 minutes of idle time triggers automatic session backup to Milvus vector store. Session context survives disconnections.
- **New: Agent Tool Usage Guide** — SKILL.md now includes usage instructions for Agent-initiated memory search.

**Plugin Changes:**

- Plugin now registers `memory_search` as a proper OpenClaw tool via `api.registerTool()`, following the same pattern as `feishu_*` tools.
- Plugin reads real session JSONL files (not the incorrect `.memory_plus_session.json`).
- Auto-store initialization logic prevents skipping on first run.
- Note: `before_prompt_build` hook remains unstable in some Gateway configurations; the cron-based auto-store is more reliable.

**Files Updated:**

- `SKILL.md` — English description for website + Agent tool usage guide
- `README.md` — Updated Chinese tagline
- `README_EN.md` — Updated English tagline
- `CHANGELOG.md` — This changelog

**Bug Fixes:**

- Plugin JS version now properly loads as CommonJS module.
- Initialization logic prevents auto-store from skipping on first run.
- Session JSONL reading fixed (was reading wrong file before).

---

### 中文

**亮点更新：**

- **新功能：`memory_search` 工具** — Agent 可主动调用 `memory_search` 工具按需搜索记忆库，不依赖 `before_prompt_build` hook。正常对话无额外延迟。
- **新功能：Cron 自动存库** — 每 5 分钟闲置后自动将 session 备份到 Milvus 向量库。断线重连不丢失上下文。
- **新功能：Agent 工具使用指南** — SKILL.md 新增 Agent 主动搜索记忆的使用说明。

**Plugin 更新：**

- Plugin 通过 `api.registerTool()` 注册 `memory_search` 工具，遵循与 `feishu_*` 工具相同的模式。
- Plugin 读取真实 session JSONL 文件（之前错误地读取了 `.memory_plus_session.json`）。
- 自动存储初始化逻辑修复，避免首次运行时误判跳过。

**文件更新：**

- `SKILL.md` — 网站展示用英文 + Agent 工具使用指南
- `README.md` — 更新中文 tagline
- `README_EN.md` — 更新英文 tagline
- `CHANGELOG.md` — 本更新日志

**问题修复：**

- Plugin JS 版本现已正确加载为 CommonJS 模块。
- 初始化逻辑修复，避免首次运行时自动存储条件误判。
- Session JSONL 读取修复（之前读取了错误的文件）。

---

## v2.0.1 (2026-03-19)

- 修复中文分词问题
- 多信号重排权重优化
- 延迟从 1200ms 降至 ~100ms

## v2.0.0 (2026-03-19)

- 多信号重排（fusion + overlap + BM25）
- 混合搜索增强
- 自动摘要生成
- 仅需 3 个环境变量配置

## v1.0.0 (2026-03-17)

- 初始版本
