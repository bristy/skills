# 🧠 Memory Plus - Enhanced Memory System

> 🧠 Provide Milvus + embedding endpoint, deploy hybrid search + reranking RAG in minutes. Conversation-triggered memory retrieval manages your context for deeper dialogue. Tiered memory: hot in session, cold in vector store.

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Architecture](#-architecture)
- [Performance](#-performance)

---

## 🎯 Features

- **Hybrid Search**: BM25 keyword + vector similarity + RRF fusion
- **Multi-Signal Rerank**: Combines fusion score, keyword overlap, and BM25 exact match
- **Auto Summary**: Auto-generates 50-char summary when storing
- **Tiered Memory**: Hot data in session, cold data in vector store
- **Lightweight**: Only requires Milvus + Ollama

---

## 📦 Requirements

### Required

| Component | Description | Docs |
|-----------|-------------|------|
| **Milvus** | Vector database for storing memory vectors | [Docs](https://milvus.io/docs/quickstart.md) |
| **Ollama** | Embedding model service | [Docs](https://ollama.com/docs) |
| **Python 3.8+** | Runtime | - |

### Python Dependencies

```bash
pip install pymilvus requests rank-bm25
```

### Recommended Config

| Config | Value | Note |
|--------|--------|------|
| Milvus Memory | 4GB+ | Allocate sufficient memory |
| Ollama Model | bge-m3 | Chinese & English bilingual |
| Collection Dimension | 1024 | bge-m3 output dimension |

---

## 🚀 Quick Start

### 1. Install

```bash
# Copy skill to your workspace
cp -r memory-plus ~/.openclaw/workspace/skills/

# Install Python dependencies
pip install pymilvus requests rank-bm25
```

### 2. Configure Environment Variables

```bash
# Milvus connection address
export MILVUS_URI=http://localhost:19530

# Ollama service address (embedding model)
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=bge-m3

# Collection name (optional, default: openclaw_memory)
export RAG_COLLECTION=openclaw_memory
```

### 3. Test

```bash
cd ~/.openclaw/workspace/skills/memory-plus

# Run self-test
python3 rag_integration.py test

# Check system status
python3 rag_integration.py status
```

Expected output:
```
[TEST] Memory Plus system test...
[OK] Stored test memory: ID xxx
[OK] Search returned 3 results
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MILVUS_URI` | ✅ | http://host.docker.internal:19530 | Milvus connection address |
| `OLLAMA_URL` | ✅ | http://host.docker.internal:11434 | Ollama API address |
| `OLLAMA_MODEL` | ✅ | bge-m3 | Embedding model name |
| `RAG_COLLECTION` | ❌ | openclaw_memory | Milvus collection name |

### Docker Deployment

**Milvus**:
```bash
# Quick single-node deployment
curl -LO https://github.com/milvus-io/milvus/releases/download/v2.4.0/milvus-standalone-docker-compose.yml
docker-compose up -d
```

**Ollama**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull embedding model
ollama pull bge-m3

# Start service
ollama serve
```

---

## 📝 Usage Examples

### Store Memory

```bash
python3 rag_integration.py store \
  --content "This is an important technical decision" \
  --source "manual" \
  --topic "tech"
```

### Search Memory

```bash
python3 rag_integration.py search \
  --query "What was the previous technical solution?" \
  --limit 5
```

### Hybrid Search Test

```bash
python3 rag_integration.py hybrid-test
```

---

## 🔧 Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────┐
│  1. Hybrid Search                            │
│                                               │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │ Vector Search   │  │ BM25 Search     │   │
│  │ (bge-m3)       │  │ (keyword match)  │   │
│  └────────┬────────┘  └────────┬────────┘   │
│           │                   │              │
│           └─────────┬─────────┘              │
│                     ▼                        │
│            RRF Rank Fusion                  │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  2. Multi-Signal Rerank                     │
│                                               │
│  Final Score =                               │
│    fused_score × 0.4  (fusion score)        │
│  + keyword_overlap × 0.3  (keyword match) │
│  + BM25 × 0.3  (exact match)               │
└─────────────────────────────────────────────┘
    │
    ▼
  Final Top-K Results
```

### Why This Design?

| Component | Role | Advantage |
|-----------|------|-----------|
| **BM25** | Exact keyword match | "RAG", "Python" terms precisely matched |
| **Vector Search** | Semantic understanding | "Deep Learning" → "DL/NN" |
| **RRF Fusion** | Stable ranking | Balances precision and semantics |
| **Multi-Signal Rerank** | Comprehensive ranking | Optimal sort from multiple signals |

---

## 📊 Performance

Based on 54 records, 15 queries:

| Metric | Value | Note |
|--------|-------|------|
| **Hit Rate** | 80%+ | Correctly retrieves relevant documents |
| **Avg Latency** | ~100ms | End-to-end search latency |
| **P95 Latency** | ~130ms | 95th percentile latency |
| **Concurrent Error Rate** | 0% | No errors under 20 concurrent requests |

---

## 🔍 FAQ

**Q: Do I need GPU?**

A: bge-m3 can run on CPU. 4GB+ RAM recommended. Larger models (like rerankers) require GPU.

**Q: Does it support Chinese?**

A: Yes! bge-m3 works well with both Chinese and English. N-gram tokenization handles Chinese text.

**Q: Will it slow down with more data?**

A: No. Milvus uses ANN indexes (IVF, HNSW), so query time is O(log N), not linear.

**Q: How to backup?**

A: Regularly backup Milvus data directory, or export to JSON.

---

## 📄 License

Inherited from OpenClaw skill license.

---

**Maintainer**: 虾宝 🦐
**Version**: 2.0.0
**Updated**: 2026-03-19
