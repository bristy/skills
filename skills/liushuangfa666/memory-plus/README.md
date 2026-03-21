# 🧠 Memory Plus - 增强记忆系统

> 🧠 增强记忆系统 — 只需提供 Milvus 和嵌入模型服务地址，即可快速部署混合检索 + 重排的 RAG 系统。对话触发记忆检索，自动管理上下文，实现深度连续对话。分层记忆：热点数据在 session，冷数据在向量库。

## 📋 目录

- [特性](#-特性)
- [部署要求](#-部署要求)
- [快速开始](#-快速开始)
- [配置说明](#-配置说明)
- [使用示例](#-使用示例)
- [技术架构](#-技术架构)
- [性能指标](#-性能指标)

---

## 🎯 特性

- **混合搜索**：BM25 关键词 + 向量相似度 + RRF 融合
- **多信号重排**：综合融合分数、关键词重叠、BM25 精确匹配
- **自动摘要**：存储时自动生成 50 字短摘要
- **分层记忆**：热数据在 session，冷数据在向量库
- **轻量部署**：仅依赖 Milvus + Ollama，无需其他服务

---

## ⚠️ 重要：Skill 与 Plugin 的关系

本 skill 包含**两个组件**，相互配合才能实现完整的自动记忆功能：

| 组件 | 文件 | 作用 |
|------|------|------|
| **Skill** | `rag_integration.py` | Python 脚本，处理 Milvus 存储/搜索的底层逻辑 |
| **Plugin** | `memory-plus-plugin` | OpenClaw 插件，注册 `before_prompt_build` hook，**自动**将记忆注入 AI 上下文 |

**如果没有 Plugin：** 只能手动运行 `store`/`search` 命令，记忆不会自动注入。
**如果没有 Skill：** Plugin 无法工作，因为 Plugin 依赖 `rag_integration.py`。

> 📦 Plugin 下载地址：https://clawhub.com（搜索 memory-plus-plugin）

## 📦 部署要求

### 必须

| 组件 | 说明 | 文档 |
|------|------|------|
| **Milvus** | 向量数据库，存储记忆向量 | [官方文档](https://milvus.io/docs/quickstart.md) |
| **Ollama** | 嵌入模型服务 | [官方文档](https://ollama.com/docs) |
| **Python 3.8+** | 运行环境和依赖 | - |

### Python 依赖

```bash
pip install pymilvus requests rank-bm25
```

### 推荐配置

| 配置 | 推荐值 | 说明 |
|------|--------|------|
| Milvus 内存 | 4GB+ | 建议分配足够内存 |
| Ollama 模型 | bge-m3 | 中英双语嵌入模型 |
| 集合维度 | 1024 | bge-m3 输出维度 |

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆或复制 skill 到你的 workspace
cp -r memory-plus ~/.openclaw/workspace/skills/

# 安装 Python 依赖
pip install pymilvus requests rank-bm25
```

### 2. 配置环境变量

```bash
# Milvus 连接地址
export MILVUS_URI=http://localhost:19530

# Ollama 服务地址（嵌入模型）
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=bge-m3

# 集合名称（可选，默认 openclaw_memory）
export RAG_COLLECTION=openclaw_memory
```

### 3. 测试

```bash
cd ~/.openclaw/workspace/skills/memory-plus

# 运行自检测试
python3 rag_integration.py test

# 查看系统状态
python3 rag_integration.py status
```

预期输出：
```
[TEST] Memory Plus system test...
[OK] Stored test memory: ID xxx
[OK] Search returned 3 results
```

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|---------|------|
| `MILVUS_URI` | ✅ | http://host.docker.internal:19530 | Milvus 连接地址 |
| `OLLAMA_URL` | ✅ | http://host.docker.internal:11434 | Ollama API 地址 |
| `OLLAMA_MODEL` | ✅ | bge-m3 | 嵌入模型名称 |
| `RAG_COLLECTION` | ❌ | openclaw_memory | Milvus 集合名 |

### Docker 部署示例

**Milvus**：
```bash
# 单节点快速部署
curl -LO https://github.com/milvus-io/milvus/releases/download/v2.4.0/milvus-standalone-docker-compose.yml
docker-compose up -d
```

**Ollama**：
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载嵌入模型
ollama pull bge-m3

# 启动服务
ollama serve
```

---

## 📝 使用示例

### 存储记忆

```bash
python3 rag_integration.py store \
  --content "这是一个重要的技术决策：我们决定使用混合搜索方案" \
  --source "manual" \
  --topic "tech"
```

### 搜索记忆

```bash
python3 rag_integration.py search \
  --query "之前的技术方案是什么" \
  --limit 5
```

### 混合搜索测试

```bash
python3 rag_integration.py hybrid-test
```

---

## 🔧 技术架构

```
用户查询
    │
    ▼
┌─────────────────────────────────────────────┐
│  1. 混合搜索 (Hybrid Search)                │
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐ │
│  │ 向量搜索        │  │ BM25 搜索       │ │
│  │ (bge-m3 嵌入)   │  │ (关键词匹配)     │ │
│  └────────┬────────┘  └────────┬────────┘ │
│           │                   │            │
│           └─────────┬─────────┘            │
│                     ▼                      │
│            RRF 排名融合                     │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  2. 多信号重排 (Multi-Signal Rerank)       │
│                                             │
│  综合评分 =                                 │
│    fused_score × 0.4  (融合分数)           │
│  + keyword_overlap × 0.3  (关键词重叠)      │
│  + BM25 × 0.3  (BM25 精确匹配)            │
└─────────────────────────────────────────────┘
    │
    ▼
  最终 Top-K 结果
```

### 为什么这样设计？

| 组件 | 作用 | 优势 |
|------|------|------|
| **BM25** | 精准关键词匹配 | "RAG"、"Python" 等术语精确命中 |
| **向量搜索** | 语义理解 | "深度学习" 能找到 "DL/NN" |
| **RRF 融合** | 排名稳定 | 兼顾精确和语义 |
| **多信号重排** | 综合排序 | 平衡多个信号得出最优排序 |

---

## 📊 性能指标

基于 54 条记忆、15 个查询的测试结果：

| 指标 | 数值 | 说明 |
|------|------|------|
| **Hit Rate** | 80%+ | 能正确召回相关文档 |
| **平均延迟** | ~100ms | 端到端搜索延迟 |
| **P95 延迟** | ~130ms | 95% 请求的延迟上限 |
| **并发错误率** | 0% | 20 并发下无错误 |

---

## 🔍 FAQ

**Q: 需要 GPU 吗？**

A: bge-m3 可以在 CPU 上运行，建议有 4GB+ 内存。如果使用更大模型（如 reranker），需要 GPU。

**Q: 支持中文吗？**

A: 支持！bge-m3 对中英文都有很好的效果。分词采用 n-gram 方式处理中文。

**Q: 数据量大了会变慢吗？**

A: Milvus 使用 ANN 索引（如 IVF、HNSW），查询时间是 O(log N)，不会随数据量线性增长。

**Q: 如何备份？**

A: 定期备份 Milvus 数据目录，或导出为 JSON。

---

## 📄 许可证

继承 OpenClaw skill 许可证。

---

**维护者**: 虾宝 🦐
**版本**: 2.0.1
**更新**: 2026-03-19
- 新增：Skill 与 Plugin 关系说明，帮助用户理解为何需要同时安装两者
