---
name: memory-plus
description: >
  🧠 OpenClaw Enhanced Memory System — Provide Milvus + embedding endpoint, deploy hybrid search + reranking RAG in minutes. Conversation-triggered memory retrieval manages your context for deeper dialogue. Tiered memory: hot in session, cold in vector store.
homepage: https://github.com/openclaw/skills
metadata:
  openclaw:
    emoji: 🧠
    requires:
      bins: [python3]
      python_pkgs: [pymilvus, requests, rank-bm25]
---

# 🧠 Memory Plus - 增强记忆系统

> 🧠 增强记忆系统 — 只需提供 Milvus 和嵌入模型服务地址，即可快速部署混合检索 + 重排的 RAG 系统。对话触发记忆检索，自动管理上下文，实现深度连续对话。分层记忆：热点数据在 session，冷数据在向量库。

---

## 🤖 Agent 工具调用（推荐方式）

**不需要 hook！Agent 可以主动调用 `memory_search` 工具来搜索记忆库。**

### 工具：memory_search

**描述：**
搜索记忆库，找到与当前对话相关的历史记忆。

**使用场景：**
- 用户提到"之前讨论过"、"还记得吗"时使用
- 需要引用之前的技术方案或决策时使用
- 开启新话题前想确认是否有相关背景时使用

**输入参数：**
- `query` (string): 搜索查询，使用当前对话的关键词或问题

**返回：** 相关记忆列表，每条包含内容摘要、时间、来源

**Agent 使用示例：**
```
当用户说"还记得我们之前讨论过什么吗"时，Agent 应主动调用：

Tool: memory_search
参数: {"query": "之前讨论过的 RAG 或 Agent 相关内容"}
```

---

## ⚙️ 架构说明

本 skill 包含**两个组件**，配合工作：

| 组件 | 文件 | 作用 |
|------|------|------|
| **Skill** | `rag_integration.py` | Python 脚本，处理 Milvus 存储/搜索底层逻辑 |
| **Plugin** | `memory-plus-plugin` | OpenClaw 插件，注册 `memory_search` 工具供 Agent 调用 + 定时自动存库 |

> 📦 Plugin 下载地址：https://clawhub.com（搜索 memory-plus-plugin）

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pymilvus requests rank-bm25
```

### 2. 配置环境变量

```bash
export MILVUS_URI=http://your-milvus:19530
export OLLAMA_URL=http://your-ollama:11434
export OLLAMA_MODEL=bge-m3
```

### 3. 安装 Plugin（开启工具 + 自动存库）

```bash
# 从 clawhub.com 下载 memory-plus-plugin
# 放置到 ~/.openclaw/extensions/memory-plus-plugin/
```

### 4. 测试

```bash
python3 rag_integration.py test
python3 rag_integration.py status
```

---

## 📖 使用方法

### Agent 主动搜索（推荐）

Agent 在回复前主动调用 `memory_search` 工具，无需用户触发：

```
用户: 记得我们上次讨论过 RAG 优化方案吗？
Agent: [调用 memory_search] → 搜 "RAG 优化方案"
     → 结合搜索结果回答
```

### 手动存储记忆

```bash
python3 rag_integration.py store \
  --content "这是一个重要的技术决策" \
  --source "manual" \
  --topic "tech"
```

### 手动搜索

```bash
python3 rag_integration.py search \
  --query "之前的技术方案是什么" \
  --limit 5
```

---

## ⚙️ 配置参数

| 环境变量 | 默认值 | 说明 |
|----------|---------|------|
| `MILVUS_URI` | http://host.docker.internal:19530 | Milvus 连接地址 |
| `RAG_COLLECTION` | openclaw_memory | Milvus 集合名 |
| `OLLAMA_URL` | http://host.docker.internal:11434 | Ollama 服务地址 |
| `OLLAMA_MODEL` | bge-m3 | 嵌入模型 |

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| Hit Rate | 80%+ |
| 平均延迟 | ~100ms（搜索） |
| P95 延迟 | ~130ms |

---

## 🔧 技术架构

```
用户查询
    ↓
┌─────────────────────────────────────┐
│  Agent 主动调用 memory_search 工具  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  混合搜索 (Hybrid Search)           │
│  - 向量相似度搜索 (bge-m3)          │
│  - BM25 关键词搜索                  │
│  - RRF 融合                        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  多信号重排 (Multi-Signal Rerank)   │
│  - fused_score × 0.4              │
│  - keyword_overlap × 0.3           │
│  - BM25 × 0.3                     │
└─────────────────────────────────────┘
    ↓
  Top-K 结果 → 注入 Agent 上下文
```

---

**版本**: 2.1.0

**更新**: 2026-03-20
- 新增：`memory_search` 工具注册，Agent 可主动调用搜索记忆
- 新增：Agent 工具调用使用说明（替代 hook 方式）
- 新增：自动定时存库（每5分钟闲置后存 session）
- 优化：营销描述中英双语
